from citereel.diff import diff_runs, format_diff
from citereel.models import Chunk, Citation, Run


def _run(**kwargs) -> Run:
    base = dict(
        query="What is the refund window?",
        retrieved=[
            Chunk(id="handbook.md#3", source="handbook.md", text="Refunds within 14 days."),
        ],
        answer="Refunds within 14 days [1].",
        citations=[Citation(n=1, chunk_id="handbook.md#3")],
        meta={"retriever": "embedding", "generator": "offline"},
    )
    base.update(kwargs)
    return Run(**base)


def test_diff_detects_answer_and_citation_drift() -> None:
    a = _run()
    b = _run(
        answer="See the FAQ [1].",
        retrieved=[
            Chunk(id="faq.md#3", source="faq.md", text="See handbook."),
        ],
        citations=[Citation(n=1, chunk_id="faq.md#3")],
        meta={"retriever": "keyword", "generator": "offline"},
    )
    d = diff_runs(a, b)
    assert d.answer_changed
    assert d.citation_delta
    assert "handbook.md#3" in d.retrieved_only_a
    assert "faq.md#3" in d.retrieved_only_b
    assert any("retriever" in line for line in d.meta_delta)
    text = format_diff(d)
    assert "answer: changed" in text
    assert "No differences" not in text


def test_identical_runs_have_empty_diff() -> None:
    a = _run()
    b = _run()
    assert diff_runs(a, b).is_empty()
    assert format_diff(diff_runs(a, b)) == "No differences."
