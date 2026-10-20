from __future__ import annotations

import hashlib
import math
import os
import re
from typing import Protocol


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
    "how",
    "i",
}


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class HashingEmbedder:
    """Local bag-of-tokens hashing vectors. No model download required."""

    def __init__(self, dims: int = 2048) -> None:
        self.dims = dims

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [_hash_vector(text, self.dims) for text in texts]


class SentenceTransformerEmbedder:
    """Optional sentence-transformers backend (slow first load)."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)
        self.model_name = model_name

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = self._model.encode(texts, normalize_embeddings=True)
        return [list(map(float, row)) for row in vectors]


def build_embedder(prefer_sentence_transformers: bool | None = None) -> Embedder:
    """Default to hashing (fast, no download). Opt into ST via env or flag.

    CITEREEL_EMBEDDER=hashing|st|sentence-transformers
    """
    if prefer_sentence_transformers is None:
        prefer_sentence_transformers = _env_wants_sentence_transformers()
    if prefer_sentence_transformers:
        try:
            return SentenceTransformerEmbedder()
        except Exception:
            pass
    return HashingEmbedder()


def _env_wants_sentence_transformers() -> bool:
    raw = (os.environ.get("CITEREEL_EMBEDDER") or "").strip().lower()
    return raw in {"st", "sentence-transformers", "sentence_transformers", "semantic"}


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _hash_vector(text: str, dims: int) -> list[float]:
    vec = [0.0] * dims
    for token in _TOKEN.findall(text.lower()):
        if len(token) <= 1 or token in _STOP:
            continue
        digest = hashlib.md5(token.encode("utf-8")).digest()
        idx = int.from_bytes(digest[:4], "little") % dims
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vec[idx] += sign
    norm = math.sqrt(sum(v * v for v in vec))
    if norm:
        vec = [v / norm for v in vec]
    return vec
