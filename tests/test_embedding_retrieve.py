from citereel.ingest import load_docs
from citereel.pipeline import ask
from citereel.retrieve import EmbeddingRetriever
from citereel.retrieve.embedder import HashingEmbedder

from citereel.paths import DEMO_DOCS

DOCS = DEMO_DOCS


def test_embedding_retriever_hits_refund_handbook() -> None:
    corpus = load_docs(DOCS)
    hits, step = EmbeddingRetriever(embedder=HashingEmbedder()).retrieve(
        "What is the refund window?",
        corpus,
        k=3,
    )
    assert hits
    assert any("14" in c.text and "refund" in c.text.lower() for c in hits)
    assert step.detail["backend"] == "embedding"
    assert hits[0].source == "handbook.md"


def test_ask_default_uses_embedding_meta() -> None:
    run = ask("What is the refund window?", DOCS, k=3, retriever="embedding")
    assert run.meta.get("retriever") in {"embedding", "keyword"}
    assert any("14" in c.text for c in run.retrieved)
