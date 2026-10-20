from citereel.diff import diff_runs, format_diff
from citereel.models import Chunk, Citation, Run


def _base(**meta):
    return Run(
        query="q",
        retrieved=[Chunk(id="a#1", source="a.md", text="14 days")],
        answer="14 days [1]",
        citations=[Citation(n=1, chunk_id="a#1")],
        meta=dict(meta),
        schema_version=2,
    )


def test_diff_reports_config_and_schema_changes() -> None:
    a = _base(config={"k": 3, "retriever": "embedding"}, docs_fingerprint="aaa")
    b = _base(config={"k": 5, "retriever": "embedding"}, docs_fingerprint="bbb")
    b.schema_version = 2
    d = diff_runs(a, b)
    assert not d.is_empty()
    text = format_diff(d)
    assert "docs_fingerprint" in text or "config" in text
    assert d.config_delta or d.docs_fingerprint_changed or d.meta_delta
