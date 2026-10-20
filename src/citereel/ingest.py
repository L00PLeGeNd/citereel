from __future__ import annotations

import os
import re
from pathlib import Path

from citereel.limits import max_chunk_chars, max_files, max_total_chars
from citereel.models import Chunk

_TEXT_SUFFIXES = {".md", ".txt"}
_PDF_SUFFIXES = {".pdf"}


def chunk_strategy() -> str:
    """paragraph (default) | page — page collapses each PDF page to one chunk."""
    value = (os.environ.get("CITEREEL_CHUNK_STRATEGY") or "paragraph").strip().lower()
    if value not in {"paragraph", "page"}:
        return "paragraph"
    return value


def load_docs(docs_dir: str | Path) -> list[Chunk]:
    """Load .md/.txt (and .pdf when pypdf is installed) with stable chunk ids."""
    root = Path(docs_dir)
    if not root.is_dir():
        raise FileNotFoundError(f"docs dir not found: {root}")

    file_cap = max_files()
    chunk_cap = max_chunk_chars()
    total_cap = max_total_chars()
    strategy = chunk_strategy()
    files_seen = 0
    total_chars = 0
    chunks: list[Chunk] = []

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        rel = str(path.relative_to(root)).replace("\\", "/")
        if suffix in _TEXT_SUFFIXES:
            text = path.read_text(encoding="utf-8", errors="replace")
            added = _chunks_from_text(rel, text, page=None, strategy=strategy, chunk_cap=chunk_cap)
        elif suffix in _PDF_SUFFIXES:
            added = _chunks_from_pdf(rel, path, strategy=strategy, chunk_cap=chunk_cap)
            if not added:
                continue
        else:
            continue

        files_seen += 1
        if files_seen > file_cap:
            raise ValueError(
                f"too many documents under {root} (limit CITEREEL_MAX_FILES={file_cap})"
            )

        for chunk in added:
            total_chars += len(chunk.text)
            if total_chars > total_cap:
                raise ValueError(
                    f"corpus too large under {root} "
                    f"(limit CITEREEL_MAX_TOTAL_CHARS={total_cap})"
                )
            chunks.append(chunk)
    if not chunks:
        raise ValueError(f"no supported documents under {root}")
    return chunks


def _chunks_from_text(
    rel: str,
    text: str,
    *,
    page: int | None,
    strategy: str,
    chunk_cap: int,
) -> list[Chunk]:
    if strategy == "page" and page is not None:
        parts = [text.strip()] if text.strip() else []
    else:
        parts = _split_paragraphs(text)
    out: list[Chunk] = []
    cursor = 0
    for index, part in enumerate(parts, start=1):
        if len(part) > chunk_cap:
            part = part[:chunk_cap].rstrip() + "..."
        start = text.find(part[:40], cursor) if part else cursor
        if start < 0:
            start = cursor
        end = start + len(part)
        cursor = end
        if page is not None:
            cid = (
                _stable_chunk_id(rel, f"p{page}")
                if strategy == "page" or len(parts) == 1
                else _stable_chunk_id(rel, f"p{page}-{index}")
            )
        else:
            cid = _stable_chunk_id(rel, str(index))
        out.append(
            Chunk(
                id=cid,
                source=rel,
                text=part,
                page=page,
                start_char=start if page is None else None,
                end_char=end if page is None else None,
            )
        )
    return out


def _chunks_from_pdf(
    rel: str,
    path: Path,
    *,
    strategy: str,
    chunk_cap: int,
) -> list[Chunk]:
    out: list[Chunk] = []
    for page_no, page_text in _iter_pdf_pages(path):
        if not page_text.strip():
            continue
        out.extend(
            _chunks_from_text(
                rel,
                page_text,
                page=page_no,
                strategy=strategy,
                chunk_cap=chunk_cap,
            )
        )
    return out


def _split_paragraphs(text: str) -> list[str]:
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return parts


def _stable_chunk_id(source: str, index: str | int) -> str:
    safe = re.sub(r"[^a-zA-Z0-9._-]+", "_", source)
    return f"{safe}#{index}"


def _iter_pdf_pages(path: Path) -> list[tuple[int, str]]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ImportError(
            "Reading PDF requires pypdf. Install with: pip install 'citereel[pdf]'"
        ) from exc
    reader = PdfReader(str(path))
    pages: list[tuple[int, str]] = []
    for index, page in enumerate(reader.pages, start=1):
        pages.append((index, page.extract_text() or ""))
    return pages
