"""Evidence evaluation: structure-valid cites can still fail semantic support."""

from citereel.evidence import ClaimJudgement, evaluate_evidence
from citereel.models import Chunk, Citation, Run


def _run(answer: str, chunk_text: str) -> Run:
    chunk = Chunk(id="handbook.md#1", source="handbook.md", text=chunk_text)
    return Run(
        query="What is the refund window?",
        retrieved=[chunk],
        answer=answer,
        citations=[Citation(n=1, chunk_id=chunk.id)],
    )


def test_structure_ok_but_wrong_conclusion_is_refuted() -> None:
    """Citation [1] exists and resolves, but the claim contradicts the passage."""
    run = _run(
        "Refunds are available for 90 days [1].",
        "Customers may request a refund within 14 days of purchase.",
    )
    report = evaluate_evidence(run)
    assert report.ok is False
    assert any(j.verdict == "refute" for j in report.judgements)
    refute = next(j for j in report.judgements if j.verdict == "refute")
    assert refute.citation_n == 1
    assert "90" in refute.claim or "90" in refute.rationale


def test_matching_claim_is_supported() -> None:
    run = _run(
        "Refunds are available within 14 days [1].",
        "Customers may request a refund within 14 days of purchase.",
    )
    report = evaluate_evidence(run)
    assert report.ok is True
    assert all(j.verdict == "support" for j in report.judgements)


def test_unrelated_claim_is_insufficient() -> None:
    run = _run(
        "Shipping is free worldwide [1].",
        "Customers may request a refund within 14 days of purchase.",
    )
    report = evaluate_evidence(run)
    assert report.ok is False
    assert any(j.verdict == "insufficient" for j in report.judgements)


def test_judgement_shape() -> None:
    j = ClaimJudgement(
        claim="x",
        citation_n=1,
        chunk_id="a#1",
        verdict="support",
        rationale="overlap",
    )
    assert j.verdict == "support"


def test_validate_structure_passes_but_evidence_flag_catches_refute() -> None:
    from citereel.validate import validate_run

    run = _run(
        "Refunds are available for 90 days [1].",
        "Customers may request a refund within 14 days of purchase.",
    )
    assert validate_run(run).ok is True
    with_evidence = validate_run(run, evidence=True)
    assert with_evidence.ok is False
    assert with_evidence.evidence_errors


def test_trailing_cite_after_period_still_judged() -> None:
    """``... purchase. [1]`` must not drop the claim from evidence checks."""
    run = _run(
        "The refund window is 90 days from purchase. [1]",
        "The refund window is 14 days from purchase.",
    )
    report = evaluate_evidence(run)
    assert report.ok is False
    assert any(j.verdict == "refute" for j in report.judgements)
