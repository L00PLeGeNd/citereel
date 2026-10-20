from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

from citereel.evidence import evaluate_evidence
from citereel.models import Run

_CITE = re.compile(r"\[(\d+)\]")
_SECRETISH = re.compile(
    r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*['\"]?[^\s'\"]{8,}"
)


@dataclass
class CheckResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    evidence_errors: list[str] = field(default_factory=list)

    def raise_if_failed(self) -> None:
        if not self.ok:
            raise ValueError("; ".join(self.errors + self.evidence_errors))


def retrieved_fingerprint(run: Run) -> str:
    digest = hashlib.sha256()
    for chunk in run.retrieved:
        digest.update(chunk.id.encode("utf-8"))
        digest.update(b"\0")
        digest.update(chunk.text.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def validate_run(run: Run, *, evidence: bool = False) -> CheckResult:
    """Structure checks (+ optional semantic evidence). Structure OK ≠ claim supported."""
    errors: list[str] = []
    warnings: list[str] = []
    evidence_errors: list[str] = []
    by_id = run.chunk_by_id()

    for cite in run.citations:
        if cite.chunk_id not in by_id:
            errors.append(f"citation [{cite.n}] points to missing chunk {cite.chunk_id!r}")
        try:
            run.resolve_citation(cite.n)
        except KeyError as exc:
            errors.append(str(exc))

    marks = sorted({int(m.group(1)) for m in _CITE.finditer(run.answer)})
    cite_ns = {c.n for c in run.citations}
    for n in marks:
        if n not in cite_ns:
            errors.append(f"answer contains [{n}] but citations map has no entry")
        else:
            try:
                run.resolve_citation(n)
            except KeyError as exc:
                errors.append(str(exc))

    if run.retrieved and run.meta.get("generator") == "openai" and not marks:
        warnings.append("openai answer has no [n] citation marks")

    if _SECRETISH.search(run.answer) or _SECRETISH.search(run.query):
        warnings.append("query/answer may contain secret-like strings")

    for step in run.steps:
        blob = str(step.detail)
        if _SECRETISH.search(blob):
            warnings.append(f"step {step.type!r} detail may contain secret-like strings")

    expected = retrieved_fingerprint(run)
    stored = run.meta.get("retrieved_sha256")
    if stored and stored != expected:
        errors.append("retrieved_sha256 mismatch (run integrity check failed)")

    if evidence:
        report = evaluate_evidence(run)
        evidence_errors.extend(report.errors)
        if report.errors:
            warnings.append(
                "evidence check found claims that citations do not support "
                "(structure may still be valid)"
            )

    return CheckResult(
        ok=not errors and not evidence_errors,
        errors=errors,
        warnings=warnings,
        evidence_errors=evidence_errors,
    )
