from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from citereel.generate import Generator, build_generator
from citereel.ingest import chunk_strategy, load_docs
from citereel.models import CURRENT_SCHEMA_VERSION, Chunk, Run
from citereel.retrieve import Retriever, build_retriever
from citereel.validate import retrieved_fingerprint, validate_run


def ask(
    query: str,
    docs_dir: str | Path,
    *,
    k: int = 3,
    retriever: Retriever | str | None = None,
    generator: Generator | str | None = None,
    model: str | None = None,
    provider: str | None = None,
    base_url: str | None = None,
    strict: bool = False,
) -> Run:
    """Load docs, retrieve, generate a cited answer, return a recordable Run."""
    corpus = load_docs(docs_dir)
    resolved_retriever = _resolve_retriever(retriever)
    resolved_generator = _resolve_generator(
        generator,
        model=model,
        provider=provider,
        base_url=base_url,
    )
    hits, retrieve_step = resolved_retriever.retrieve(query, corpus, k=k)
    answer, citations, generate_step = resolved_generator.generate(query, hits)
    config: dict[str, Any] = {
        "k": k,
        "retriever": retrieve_step.detail.get("backend", type(resolved_retriever).__name__),
        "generator": generate_step.detail.get("mode", type(resolved_generator).__name__),
        "chunk_strategy": chunk_strategy(),
        "docs_dir": str(Path(docs_dir)),
    }
    for key in ("model", "provider"):
        if key in generate_step.detail:
            config[key] = generate_step.detail[key]
    meta: dict[str, Any] = {
        "retriever": config["retriever"],
        "generator": config["generator"],
        "corpus_chunks": len(corpus),
        "assist_mode": "human_review",
        "config": config,
        "docs_fingerprint": corpus_fingerprint(corpus),
        "replay_mode": "offline",
    }
    for key in ("model", "provider"):
        if key in generate_step.detail:
            meta[key] = generate_step.detail[key]
    run = Run(
        query=query,
        retrieved=hits,
        answer=answer,
        citations=citations,
        steps=[retrieve_step, generate_step],
        schema_version=CURRENT_SCHEMA_VERSION,
        meta=meta,
    )
    run.meta["retrieved_sha256"] = retrieved_fingerprint(run)
    check = validate_run(run)
    run.meta["validation_ok"] = check.ok
    if check.warnings:
        run.meta["validation_warnings"] = check.warnings
    if check.errors:
        run.meta["validation_errors"] = check.errors
    if strict:
        check.raise_if_failed()
    return run


def corpus_fingerprint(chunks: list[Chunk]) -> str:
    digest = hashlib.sha256()
    for chunk in chunks:
        digest.update(chunk.id.encode("utf-8"))
        digest.update(b"\0")
        digest.update(chunk.text.encode("utf-8"))
        digest.update(b"\0")
        if chunk.page is not None:
            digest.update(str(chunk.page).encode("utf-8"))
            digest.update(b"\0")
    return digest.hexdigest()


def _resolve_retriever(retriever: Retriever | str | None) -> Retriever:
    if retriever is None:
        return build_retriever("embedding")
    if isinstance(retriever, str):
        return build_retriever(retriever)
    return retriever


def _resolve_generator(
    generator: Generator | str | None,
    *,
    model: str | None = None,
    provider: str | None = None,
    base_url: str | None = None,
) -> Generator:
    if generator is None:
        return build_generator("auto", model=model, provider=provider, base_url=base_url)
    if isinstance(generator, str):
        return build_generator(generator, model=model, provider=provider, base_url=base_url)
    return generator
