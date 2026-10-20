from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from typing import Any
import json
import time
import uuid

SUPPORTED_SCHEMA_VERSIONS = frozenset({1, 2})
CURRENT_SCHEMA_VERSION = 2


class RunSchemaError(ValueError):
    """Raised when a run.json fails structural / schema checks."""


@dataclass
class Chunk:
    id: str
    source: str
    text: str
    page: int | None = None
    section: str | None = None
    start_char: int | None = None
    end_char: int | None = None


@dataclass
class Citation:
    n: int
    chunk_id: str


@dataclass
class Step:
    type: str
    ms: float
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class Run:
    query: str
    retrieved: list[Chunk]
    answer: str
    citations: list[Citation]
    steps: list[Step] = field(default_factory=list)
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: float = field(default_factory=time.time)
    schema_version: int = CURRENT_SCHEMA_VERSION
    meta: dict[str, Any] = field(default_factory=dict)

    def chunk_by_id(self) -> dict[str, Chunk]:
        return {chunk.id: chunk for chunk in self.retrieved}

    def resolve_citation(self, n: int) -> Chunk:
        """Return the chunk linked to citation number `n`."""
        for cite in self.citations:
            if cite.n == n:
                chunk = self.chunk_by_id().get(cite.chunk_id)
                if chunk is None:
                    raise KeyError(f"citation {n} points to missing chunk {cite.chunk_id!r}")
                return chunk
        raise KeyError(f"citation {n} not found")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "id": self.id,
            "created_at": self.created_at,
            "query": self.query,
            "retrieved": [_chunk_to_dict(c) for c in self.retrieved],
            "answer": self.answer,
            "citations": [asdict(c) for c in self.citations],
            "steps": [asdict(s) for s in self.steps],
            "meta": self.meta,
        }

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: str) -> Run:
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as exc:
            raise RunSchemaError(f"invalid JSON in {path}: {exc}") from exc
        except OSError as exc:
            raise RunSchemaError(f"cannot read {path}: {exc}") from exc
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Any) -> Run:
        if not isinstance(data, dict):
            raise RunSchemaError("run document must be a JSON object")
        version = data.get("schema_version", 1)
        try:
            version_i = int(version)
        except (TypeError, ValueError) as exc:
            raise RunSchemaError(f"schema_version must be an int, got {version!r}") from exc
        if version_i not in SUPPORTED_SCHEMA_VERSIONS:
            raise RunSchemaError(
                f"unsupported schema_version {version_i}; "
                f"supported={sorted(SUPPORTED_SCHEMA_VERSIONS)}"
            )
        for key in ("query", "answer"):
            if key not in data:
                raise RunSchemaError(f"missing required field {key!r}")
            if not isinstance(data[key], str):
                raise RunSchemaError(f"{key} must be a string")
        retrieved_raw = data.get("retrieved", [])
        citations_raw = data.get("citations", [])
        steps_raw = data.get("steps", [])
        if not isinstance(retrieved_raw, list):
            raise RunSchemaError("retrieved must be a list")
        if not isinstance(citations_raw, list):
            raise RunSchemaError("citations must be a list")
        if not isinstance(steps_raw, list):
            raise RunSchemaError("steps must be a list")
        meta = data.get("meta") or {}
        if not isinstance(meta, dict):
            raise RunSchemaError("meta must be an object")
        try:
            retrieved = [_chunk_from_dict(c) for c in retrieved_raw]
            citations = [Citation(**_pick(Citation, c)) for c in citations_raw]
            steps = [Step(**_pick(Step, c)) for c in steps_raw]
        except (TypeError, KeyError, ValueError) as exc:
            raise RunSchemaError(f"invalid run payload: {exc}") from exc
        return cls(
            schema_version=version_i,
            id=str(data.get("id") or uuid.uuid4().hex[:12]),
            created_at=float(data.get("created_at") or time.time()),
            query=data["query"],
            retrieved=retrieved,
            answer=data["answer"],
            citations=citations,
            steps=steps,
            meta=dict(meta),
        )


def _pick(cls: type, data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise RunSchemaError(f"expected object for {cls.__name__}")
    names = {f.name for f in fields(cls)}
    return {k: v for k, v in data.items() if k in names}


def _chunk_from_dict(data: Any) -> Chunk:
    picked = _pick(Chunk, data)
    for required in ("id", "source", "text"):
        if required not in picked:
            raise RunSchemaError(f"chunk missing {required!r}")
    return Chunk(**picked)


def _chunk_to_dict(chunk: Chunk) -> dict[str, Any]:
    payload = asdict(chunk)
    return {k: v for k, v in payload.items() if v is not None}
