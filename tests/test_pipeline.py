from pathlib import Path

from citereel.models import Run
from citereel.paths import DEMO_DOCS
from citereel.pipeline import ask

DOCS = DEMO_DOCS


def test_ask_returns_citations_for_refund_query(tmp_path: Path) -> None:
    run = ask("What is the refund window?", DOCS, k=3)
    assert run.citations
    assert "[1]" in run.answer or run.citations[0].n == 1
    assert any("14" in c.text for c in run.retrieved)

    out = tmp_path / "run.json"
    run.save(str(out))
    loaded = Run.load(str(out))
    assert loaded.query == run.query
    assert loaded.citations[0].chunk_id == run.citations[0].chunk_id


def test_citation_chunk_ids_exist_in_retrieved() -> None:
    run = ask("What is the refund window?", DOCS, k=3)
    ids = {c.id for c in run.retrieved}
    for cite in run.citations:
        assert cite.chunk_id in ids


def test_ask_records_repro_fingerprints() -> None:
    from citereel import __version__

    run = ask(
        "What is the refund window?",
        DOCS,
        k=3,
        retriever="embedding",
        generator="offline",
    )
    cfg = run.meta["config"]
    assert cfg["k"] == 3
    assert cfg["retriever"] == "embedding"
    assert cfg["generator"] == "offline"
    assert cfg["chunk_strategy"] in {"paragraph", "page"}
    assert cfg["max_chunk_chars"] >= 1
    assert cfg["citereel_version"] == __version__
    assert cfg["embedder"]  # e.g. HashingEmbedder
    assert run.meta["citereel_version"] == __version__
    assert run.meta["docs_fingerprint"]
    assert len(run.meta["docs_fingerprint"]) == 64
