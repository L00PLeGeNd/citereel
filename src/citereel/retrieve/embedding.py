from __future__ import annotations

import hashlib
import time

from citereel.models import Chunk, Step
from citereel.retrieve.embedder import Embedder, HashingEmbedder, build_embedder, cosine
from citereel.retrieve.keyword import KeywordRetriever, tokens as lexical_tokens


class EmbeddingRetriever:
    """Dense/hashing similarity over chunk text. Falls back to keyword on failure."""

    def __init__(
        self,
        embedder: Embedder | None = None,
        *,
        fallback_to_keyword: bool = True,
    ) -> None:
        self.embedder = embedder or build_embedder()
        self.fallback_to_keyword = fallback_to_keyword
        self._backend = type(self.embedder).__name__
        self._cache_key: str | None = None
        self._cache_vectors: list[list[float]] | None = None

    def retrieve(
        self,
        query: str,
        corpus: list[Chunk],
        *,
        k: int = 3,
    ) -> tuple[list[Chunk], Step]:
        try:
            return self._retrieve_embedding(query, corpus, k=k)
        except Exception as exc:
            if not self.fallback_to_keyword:
                raise
            hits, step = KeywordRetriever().retrieve(query, corpus, k=k)
            step.detail["backend"] = "keyword"
            step.detail["fallback_from"] = self._backend
            step.detail["fallback_reason"] = str(exc)
            return hits, step

    def _retrieve_embedding(
        self,
        query: str,
        corpus: list[Chunk],
        *,
        k: int,
    ) -> tuple[list[Chunk], Step]:
        t0 = time.perf_counter()
        if not corpus:
            step = Step(type="retrieve", ms=0.0, detail={"k": k, "chunk_ids": [], "backend": "embedding"})
            return [], step

        vectors, cache_hit = self._corpus_vectors(corpus)
        qvec = self.embedder.embed([query])[0]
        q_tokens = lexical_tokens(query)
        scored: list[tuple[float, Chunk]] = []
        for vec, chunk in zip(vectors, corpus, strict=True):
            score = cosine(qvec, vec)
            # Hashing collisions are common on tiny corpora; blend lexical overlap.
            if isinstance(self.embedder, HashingEmbedder) and q_tokens:
                overlap = len(q_tokens & lexical_tokens(chunk.text)) / len(q_tokens)
                score = 0.35 * score + 0.65 * overlap
            scored.append((score, chunk))
        scored.sort(key=lambda item: item[0], reverse=True)
        ranked = [chunk for score, chunk in scored[:k] if score > 0] or [chunk for _, chunk in scored[:k]]
        ms = (time.perf_counter() - t0) * 1000
        step = Step(
            type="retrieve",
            ms=round(ms, 2),
            detail={
                "k": k,
                "chunk_ids": [c.id for c in ranked],
                "backend": "embedding",
                "embedder": self._backend,
                "top_score": round(scored[0][0], 4) if scored else 0.0,
                "cache_hit": cache_hit,
            },
        )
        return ranked, step

    def _corpus_vectors(self, corpus: list[Chunk]) -> tuple[list[list[float]], bool]:
        key = _corpus_fingerprint(corpus)
        if self._cache_key == key and self._cache_vectors is not None:
            return self._cache_vectors, True
        vectors = self.embedder.embed([c.text for c in corpus])
        self._cache_key = key
        self._cache_vectors = vectors
        return vectors, False


def default_embedding_retriever() -> EmbeddingRetriever:
    """Fast local hashing by default; set CITEREEL_EMBEDDER=st for semantic models."""
    return EmbeddingRetriever(embedder=build_embedder())


def _corpus_fingerprint(corpus: list[Chunk]) -> str:
    digest = hashlib.sha1()
    for chunk in corpus:
        digest.update(chunk.id.encode("utf-8"))
        digest.update(b"\0")
        digest.update(chunk.text.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()
