from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class CaseResult:
    case_id: str
    query: str
    passed: bool
    structure_ok: bool
    evidence_ok: bool
    gold_ok: bool
    latency_ms: float
    failures: list[str] = field(default_factory=list)
    failure_kinds: list[str] = field(default_factory=list)
    run_id: str = ""
    answer_preview: str = ""
    config_snapshot: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SuiteReport:
    suite_id: str
    config_name: str
    cases: list[CaseResult]
    docs_fingerprint: str = ""
    total_latency_ms: float = 0.0

    @property
    def passed_count(self) -> int:
        return sum(1 for c in self.cases if c.passed)

    @property
    def total(self) -> int:
        return len(self.cases)

    def to_dict(self) -> dict[str, Any]:
        return {
            "suite_id": self.suite_id,
            "config_name": self.config_name,
            "docs_fingerprint": self.docs_fingerprint,
            "total_latency_ms": self.total_latency_ms,
            "passed": self.passed_count,
            "total": self.total,
            "cases": [c.to_dict() for c in self.cases],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SuiteReport:
        cases = [
            CaseResult(
                case_id=str(c["case_id"]),
                query=str(c.get("query") or ""),
                passed=bool(c.get("passed")),
                structure_ok=bool(c.get("structure_ok")),
                evidence_ok=bool(c.get("evidence_ok")),
                gold_ok=bool(c.get("gold_ok", True)),
                latency_ms=float(c.get("latency_ms") or 0),
                failures=list(c.get("failures") or []),
                failure_kinds=list(c.get("failure_kinds") or []),
                run_id=str(c.get("run_id") or ""),
                answer_preview=str(c.get("answer_preview") or ""),
                config_snapshot=dict(c.get("config_snapshot") or {}),
            )
            for c in data.get("cases") or []
        ]
        return cls(
            suite_id=str(data.get("suite_id") or ""),
            config_name=str(data.get("config_name") or "prior"),
            cases=cases,
            docs_fingerprint=str(data.get("docs_fingerprint") or ""),
            total_latency_ms=float(data.get("total_latency_ms") or 0),
        )
