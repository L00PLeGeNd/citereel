"""Bundled “gotcha” run: citations look fine, evidence check fails.

Used by `citereel catch` so newcomers see the product value in seconds —
without an API key or a custom corpus.
"""

from __future__ import annotations

from citereel.ingest import load_docs
from citereel.models import Citation, CURRENT_SCHEMA_VERSION, Run, Step
from citereel.paths import DEMO_DOCS


def build_catch_run() -> Run:
    """Craft a run that maps [1] to a real chunk but invents a wrong number."""
    corpus = load_docs(DEMO_DOCS)
    chunk = next(
        (
            c
            for c in corpus
            if "14" in c.text and "refund" in c.text.lower()
        ),
        None,
    )
    if chunk is None:  # pragma: no cover - bundled docs always have this
        raise RuntimeError("bundled demo docs missing refund window passage")

    answer = "The refund window is 90 days from purchase. [1]"
    return Run(
        query="What is the refund window?",
        retrieved=[chunk],
        answer=answer,
        citations=[Citation(n=1, chunk_id=chunk.id)],
        steps=[
            Step(
                type="retrieve",
                ms=0.0,
                detail={"k": 1, "chunk_ids": [chunk.id], "backend": "demo-catch"},
            ),
            Step(
                type="generate",
                ms=0.0,
                detail={"mode": "demo-catch", "note": "intentionally wrong number"},
            ),
        ],
        schema_version=CURRENT_SCHEMA_VERSION,
        meta={
            "retriever": "demo-catch",
            "generator": "demo-catch",
            "assist_mode": "human_review",
            "catch_demo": True,
            "config": {
                "retriever": "demo-catch",
                "generator": "demo-catch",
                "note": "synthetic wrong-number answer over a real handbook chunk",
            },
        },
    )
