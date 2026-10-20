import pytest

from citereel.models import Run
from citereel.pipeline import ask

from citereel.paths import DEMO_DOCS

DOCS = DEMO_DOCS


def test_resolve_citation_returns_matching_chunk() -> None:
    run = ask("What is the refund window?", DOCS, k=3, generator="offline", retriever="embedding")
    chunk = run.resolve_citation(1)
    assert chunk.id == run.citations[0].chunk_id
    assert any("14" in run.resolve_citation(c.n).text for c in run.citations)


def test_resolve_citation_unknown_raises() -> None:
    run = ask("What is the refund window?", DOCS, k=3, generator="offline")
    with pytest.raises(KeyError, match="citation"):
        run.resolve_citation(99)
