from __future__ import annotations

import re
import time

from citereel.models import Chunk, Step

_TOKEN = re.compile(r"[a-z0-9\u4e00-\u9fff]+", re.I)
_STOP = {
    "a",
    "an",
    "the",
    "is",
    "are",
    "was",
    "were",
    "what",
    "which",
    "who",
    "whom",
    "do",
    "does",
    "did",
    "of",
    "in",
    "on",
    "for",
    "to",
    "and",
    "or",
}


def tokens(text: str) -> set[str]:
    return {
        t.lower()
        for t in _TOKEN.findall(text)
        if t.lower() not in _STOP and len(t) > 1
    }


_tokens = tokens  # backward alias for internal callers


class KeywordRetriever:
    """Overlap score over tokenized text. Good enough for demos; swap later."""

    def retrieve(
        self,
        query: str,
        corpus: list[Chunk],
        *,
        k: int = 3,
    ) -> tuple[list[Chunk], Step]:
        t0 = time.perf_counter()
        q = tokens(query)
        if not q:
            ranked = corpus[:k]
        else:
            scored: list[tuple[float, Chunk]] = []
            for chunk in corpus:
                overlap = len(q & tokens(chunk.text))
                if overlap:
                    scored.append((overlap / len(q), chunk))
            scored.sort(key=lambda item: item[0], reverse=True)
            ranked = [chunk for _, chunk in scored[:k]] or corpus[:k]
        ms = (time.perf_counter() - t0) * 1000
        step = Step(
            type="retrieve",
            ms=round(ms, 2),
            detail={"k": k, "chunk_ids": [c.id for c in ranked], "backend": "keyword"},
        )
        return ranked, step
