"""Score a recorded run against an eval case; classify failure kinds."""

from __future__ import annotations

from citereel.eval.dataset import EvalCase
from citereel.evidence import evaluate_evidence
from citereel.models import Run
from citereel.validate import validate_run


def score_case(case: EvalCase, run: Run) -> tuple[bool, bool, bool, list[str], list[str]]:
    """Return structure_ok, evidence_ok, gold_ok, failures, failure_kinds."""
    failures: list[str] = []
    kinds: list[str] = []

    structural = validate_run(run, evidence=False)
    structure_ok = structural.ok
    if not structure_ok:
        kinds.append("structure")
        failures.extend(structural.errors)

    evidence_report = evaluate_evidence(run)
    evidence_ok = evidence_report.ok
    if case.expect_evidence_ok is True and not evidence_ok:
        kinds.append("evidence")
        failures.extend(evidence_report.errors)
    elif case.expect_evidence_ok is False and evidence_ok and run.citations:
        # Rare: case expects weak evidence; treat unexpected full support as soft fail.
        pass

    if case.expect_citations is True and not run.citations:
        kinds.append("generation")
        failures.append("expected citations but answer had none")
        structure_ok = False
    if case.expect_citations is False and run.citations:
        kinds.append("generation")
        failures.append("expected no citations but answer cited passages")

    gold_ok = True
    answer_l = run.answer.lower()
    for needle in case.gold_answer_contains:
        if needle.lower() not in answer_l:
            gold_ok = False
            kinds.append("generation")
            failures.append(f"answer missing gold token {needle!r}")

    for needle in case.forbid_answer_contains:
        if needle.lower() in answer_l:
            gold_ok = False
            kinds.append("generation")
            failures.append(f"answer contains forbidden token {needle!r}")

    if case.gold_evidence_contains:
        blob = " ".join(c.text for c in run.retrieved).lower()
        for needle in case.gold_evidence_contains:
            if needle.lower() not in blob:
                gold_ok = False
                kinds.append("retrieval")
                failures.append(f"retrieved evidence missing {needle!r}")

    # Deduplicate kinds while preserving order
    seen: set[str] = set()
    uniq_kinds: list[str] = []
    for k in kinds:
        if k not in seen:
            seen.add(k)
            uniq_kinds.append(k)

    expectations_met = True
    if case.expect_evidence_ok is True and not evidence_ok:
        expectations_met = False
    if case.expect_citations is True and not run.citations:
        expectations_met = False
    if case.expect_citations is False and run.citations:
        expectations_met = False

    passed = structure_ok and gold_ok and expectations_met
    if case.expect_evidence_ok is True:
        passed = passed and evidence_ok

    return structure_ok, evidence_ok, gold_ok, failures, uniq_kinds
