from __future__ import annotations

from typing import Protocol

from citereel.models import Chunk, Citation, Step


class Generator(Protocol):
    """Turn retrieved chunks into an answer plus citation links."""

    def generate(
        self,
        query: str,
        retrieved: list[Chunk],
    ) -> tuple[str, list[Citation], Step]: ...
