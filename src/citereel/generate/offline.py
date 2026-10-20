from __future__ import annotations

import re
import time

from citereel.models import Chunk, Citation, Step
from citereel.retrieve.keyword import tokens as lexical_tokens

_SENTENCE = re.compile(r"(?<=[.!?。！？])\s+|\n+")


class OfflineGenerator:
    """No LLM: quote the most query-relevant sentence and cite that chunk."""

    def generate(
        self,
        query: str,
        retrieved: list[Chunk],
    ) -> tuple[str, list[Citation], Step]:
        t0 = time.perf_counter()
        if not retrieved:
            answer = "I could not find supporting documents for that question."
            citations: list[Citation] = []
        else:
            best_index = _best_chunk_index(query, retrieved)
            best = retrieved[best_index]
            n = best_index + 1
            snippet = _best_snippet(query, best.text, limit=180)
            answer = f"{snippet} [{n}]"
            # Keep a full map so show N still works for every retrieved chunk.
            citations = [
                Citation(n=i + 1, chunk_id=chunk.id) for i, chunk in enumerate(retrieved)
            ]
        ms = (time.perf_counter() - t0) * 1000
        step = Step(
            type="generate",
            ms=round(ms, 2),
            detail={"mode": "offline", "query": query},
        )
        return answer, citations, step


def _best_chunk_index(query: str, chunks: list[Chunk]) -> int:
    q = lexical_tokens(query)
    if not q:
        return 0
    scores = [len(q & lexical_tokens(chunk.text)) / len(q) for chunk in chunks]
    return max(range(len(chunks)), key=lambda i: scores[i])


def _best_snippet(query: str, text: str, *, limit: int) -> str:
    q = lexical_tokens(query)
    parts = [p.strip() for p in _SENTENCE.split(text) if p.strip()]
    if not parts:
        return _shorten(text, limit)
    if not q:
        return _shorten(parts[0], limit)

    def score(part: str) -> float:
        return len(q & lexical_tokens(part)) / len(q)

    best = max(parts, key=score)
    if score(best) <= 0:
        best = parts[0]
    return _shorten(best, limit)


def _shorten(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."
