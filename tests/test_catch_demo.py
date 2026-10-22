"""Public seam: catch demo proves structure OK ≠ evidence OK."""

from citereel.catch_demo import build_catch_run
from citereel.validate import validate_run


def test_catch_run_structure_ok_evidence_fails() -> None:
    run = build_catch_run()
    assert "[1]" in run.answer
    assert run.citations
    assert validate_run(run, evidence=False).ok is True
    with_e = validate_run(run, evidence=True)
    assert with_e.ok is False
    assert with_e.evidence_errors
    blob = " ".join(with_e.evidence_errors).lower()
    assert "90" in blob or "refute" in blob
