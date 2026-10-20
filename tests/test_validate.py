from citereel.models import Chunk, Citation, Run
from citereel.validate import retrieved_fingerprint, validate_run


def _run(**kwargs) -> Run:
    base = dict(
        query="What is the refund window?",
        retrieved=[
            Chunk(id="handbook.md#3", source="handbook.md", text="The refund window is 14 days."),
        ],
        answer="The refund window is 14 days [1].",
        citations=[Citation(n=1, chunk_id="handbook.md#3")],
        meta={"generator": "openai"},
    )
    base.update(kwargs)
    run = Run(**base)
    run.meta["retrieved_sha256"] = retrieved_fingerprint(run)
    return run


def test_validate_ok() -> None:
    result = validate_run(_run())
    assert result.ok
    assert not result.errors


def test_validate_detects_missing_chunk() -> None:
    run = _run(citations=[Citation(n=1, chunk_id="missing")])
    result = validate_run(run)
    assert not result.ok
    assert result.errors


def test_validate_detects_answer_mark_without_map() -> None:
    run = _run(answer="See [2].", citations=[Citation(n=1, chunk_id="handbook.md#3")])
    result = validate_run(run)
    assert not result.ok


def test_fingerprint_changes_with_text() -> None:
    a = _run()
    b = _run(
        retrieved=[
            Chunk(id="handbook.md#3", source="handbook.md", text="changed"),
        ]
    )
    assert retrieved_fingerprint(a) != retrieved_fingerprint(b)
