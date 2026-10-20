from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from citereel.paths import DEMO_DOCS


@dataclass(frozen=True)
class EvalCase:
    id: str
    query: str
    gold_answer_contains: tuple[str, ...] = ()
    gold_evidence_contains: tuple[str, ...] = ()
    forbid_answer_contains: tuple[str, ...] = ()
    expect_citations: bool | None = None
    expect_evidence_ok: bool | None = None
    notes: str = ""


@dataclass(frozen=True)
class EvalSuite:
    id: str
    cases: tuple[EvalCase, ...]
    docs: str | None = None
    description: str = ""
    schema_version: int = 1
    path: Path | None = None

    def resolve_docs(self) -> Path:
        if self.docs:
            return Path(self.docs).expanduser().resolve()
        return DEMO_DOCS.resolve()

    @classmethod
    def from_dict(cls, data: dict[str, Any], *, path: Path | None = None) -> EvalSuite:
        if not isinstance(data, dict):
            raise ValueError("eval suite must be a JSON object")
        cases_raw = data.get("cases")
        if not isinstance(cases_raw, list) or not cases_raw:
            raise ValueError("eval suite needs a non-empty cases list")
        cases: list[EvalCase] = []
        for raw in cases_raw:
            if not isinstance(raw, dict) or "id" not in raw or "query" not in raw:
                raise ValueError("each case needs id and query")
            cases.append(
                EvalCase(
                    id=str(raw["id"]),
                    query=str(raw["query"]),
                    gold_answer_contains=tuple(raw.get("gold_answer_contains") or ()),
                    gold_evidence_contains=tuple(raw.get("gold_evidence_contains") or ()),
                    forbid_answer_contains=tuple(raw.get("forbid_answer_contains") or ()),
                    expect_citations=raw.get("expect_citations"),
                    expect_evidence_ok=raw.get("expect_evidence_ok"),
                    notes=str(raw.get("notes") or ""),
                )
            )
        return cls(
            id=str(data.get("id") or "suite"),
            cases=tuple(cases),
            docs=data.get("docs"),
            description=str(data.get("description") or ""),
            schema_version=int(data.get("schema_version") or 1),
            path=path,
        )


def load_suite(path: str | Path) -> EvalSuite:
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    return EvalSuite.from_dict(data, path=p.resolve())
