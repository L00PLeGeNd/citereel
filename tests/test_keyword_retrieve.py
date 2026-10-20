from citereel.ingest import load_docs
from citereel.retrieve import KeywordRetriever

from citereel.paths import DEMO_DOCS

DOCS = DEMO_DOCS


def test_refund_query_prefers_handbook_chunk() -> None:
    corpus = load_docs(DOCS)
    hits, step = KeywordRetriever().retrieve("What is the refund window?", corpus, k=3)
    assert hits
    assert any("14" in chunk.text and "refund" in chunk.text.lower() for chunk in hits)
    assert step.detail["backend"] == "keyword"
    assert hits[0].source == "handbook.md"
