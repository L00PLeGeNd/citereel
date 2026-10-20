from __future__ import annotations

from typing import Protocol

from citereel.models import Chunk, Step


class Retriever(Protocol):
    """Select chunks for a query. Implementations may use keywords, embeddings, etc."""

    def retrieve(
        self,
        query: str,
        corpus: list[Chunk],
        *,
        k: int = 3,
    ) -> tuple[list[Chunk], Step]: ...
