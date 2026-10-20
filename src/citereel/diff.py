from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from citereel.models import Run


@dataclass(frozen=True)
class RunDiff:
    query_changed: bool
    answer_changed: bool
    citation_delta: list[str]
    retrieved_only_a: list[str]
    retrieved_only_b: list[str]
    meta_delta: list[str]
    schema_changed: bool = False
    docs_fingerprint_changed: bool = False
    config_delta: list[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not (
            self.query_changed
            or self.answer_changed
            or self.citation_delta
            or self.retrieved_only_a
            or self.retrieved_only_b
            or self.meta_delta
            or self.schema_changed
            or self.docs_fingerprint_changed
            or self.config_delta
        )


def diff_runs(a: Run, b: Run) -> RunDiff:
    """Compare two recorded runs for query/answer/citation/retrieved/meta/config drift."""
    cites_a = {(c.n, c.chunk_id) for c in a.citations}
    cites_b = {(c.n, c.chunk_id) for c in b.citations}
    citation_delta: list[str] = []
    for n, chunk_id in sorted(cites_a - cites_b):
        citation_delta.append(f"- [{n}] {chunk_id}")
    for n, chunk_id in sorted(cites_b - cites_a):
        citation_delta.append(f"+ [{n}] {chunk_id}")

    ids_a = {c.id for c in a.retrieved}
    ids_b = {c.id for c in b.retrieved}

    meta_delta: list[str] = []
    skip_meta = {"config", "docs_fingerprint"}
    keys = sorted((set(a.meta) | set(b.meta)) - skip_meta)
    for key in keys:
        va = a.meta.get(key)
        vb = b.meta.get(key)
        if va != vb:
            meta_delta.append(f"{key}: {va!r} -> {vb!r}")

    config_delta = _dict_delta(a.meta.get("config") or {}, b.meta.get("config") or {})
    docs_a = a.meta.get("docs_fingerprint")
    docs_b = b.meta.get("docs_fingerprint")

    return RunDiff(
        query_changed=a.query != b.query,
        answer_changed=a.answer != b.answer,
        citation_delta=citation_delta,
        retrieved_only_a=sorted(ids_a - ids_b),
        retrieved_only_b=sorted(ids_b - ids_a),
        meta_delta=meta_delta,
        schema_changed=a.schema_version != b.schema_version,
        docs_fingerprint_changed=docs_a != docs_b and (docs_a is not None or docs_b is not None),
        config_delta=config_delta,
    )


def format_diff(diff: RunDiff, *, label_a: str = "a", label_b: str = "b") -> str:
    if diff.is_empty():
        return "No differences."
    lines: list[str] = []
    if diff.schema_changed:
        lines.append("schema_version: changed")
    if diff.query_changed:
        lines.append("query: changed")
    if diff.answer_changed:
        lines.append("answer: changed")
    if diff.docs_fingerprint_changed:
        lines.append("docs_fingerprint: changed")
    if diff.config_delta:
        lines.append("config:")
        lines.extend(f"  {line}" for line in diff.config_delta)
    if diff.citation_delta:
        lines.append("citations:")
        lines.extend(f"  {line}" for line in diff.citation_delta)
    if diff.retrieved_only_a:
        lines.append(f"retrieved only in {label_a}:")
        lines.extend(f"  - {cid}" for cid in diff.retrieved_only_a)
    if diff.retrieved_only_b:
        lines.append(f"retrieved only in {label_b}:")
        lines.extend(f"  + {cid}" for cid in diff.retrieved_only_b)
    if diff.meta_delta:
        lines.append("meta:")
        lines.extend(f"  {line}" for line in diff.meta_delta)
    return "\n".join(lines)


def _dict_delta(a: Any, b: Any) -> list[str]:
    if not isinstance(a, dict):
        a = {}
    if not isinstance(b, dict):
        b = {}
    lines: list[str] = []
    for key in sorted(set(a) | set(b)):
        if a.get(key) != b.get(key):
            lines.append(f"{key}: {a.get(key)!r} -> {b.get(key)!r}")
    return lines
