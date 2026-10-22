from citereel.diff import diff_runs, format_diff
from citereel.models import Chunk, Citation, Run
from citereel.replay import format_replay_banner


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


def test_diff_surfaces_embedder_and_version_in_config() -> None:
    a = _base(
        config={
            "k": 3,
            "retriever": "embedding",
            "embedder": "HashingEmbedder",
            "citereel_version": "0.1.0",
            "chunk_strategy": "paragraph",
            "max_chunk_chars": 8000,
        },
        docs_fingerprint="aaa",
        citereel_version="0.1.0",
    )
    b = _base(
        config={
            "k": 3,
            "retriever": "embedding",
            "embedder": "SentenceTransformerEmbedder",
            "citereel_version": "0.1.1",
            "chunk_strategy": "page",
            "max_chunk_chars": 4000,
        },
        docs_fingerprint="aaa",
        citereel_version="0.1.1",
    )
    text = format_diff(diff_runs(a, b))
    assert "embedder" in text
    assert "citereel_version" in text
    assert "chunk_strategy" in text
    assert "max_chunk_chars" in text


def test_replay_banner_lists_repro_fields() -> None:
    run = _base(
        config={
            "k": 3,
            "retriever": "embedding",
            "generator": "offline",
            "embedder": "HashingEmbedder",
            "chunk_strategy": "paragraph",
            "max_chunk_chars": 8000,
            "citereel_version": "0.1.0",
        },
        docs_fingerprint="abcd" * 16,
        citereel_version="0.1.0",
        replay_mode="offline",
    )
    banner = format_replay_banner(run)
    assert "schema=2" in banner
    assert "docs_fp=abcdabcdabcd" in banner
    assert "embedding" in banner
    assert "HashingEmbedder" in banner
    assert "citereel=0.1.0" in banner
    assert "chunk=paragraph" in banner
