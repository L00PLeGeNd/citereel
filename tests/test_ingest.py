from citereel.ingest import load_docs
from citereel.paths import DEMO_DOCS

DOCS = DEMO_DOCS


def test_chunk_ids_are_stable_and_source_scoped() -> None:
    chunks = load_docs(DOCS)
    assert chunks
    assert all("#" in c.id for c in chunks)
    handbook = [c for c in chunks if c.source == "handbook.md"]
    assert handbook
    assert handbook[0].id.startswith("handbook.md#")
    ids = [c.id for c in chunks]
    assert len(ids) == len(set(ids))
