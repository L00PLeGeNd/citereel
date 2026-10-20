from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

from citereel.eval.dataset import EvalSuite
from citereel.eval.report import CaseResult, SuiteReport
from citereel.eval.score import score_case
from citereel.pipeline import ask, corpus_fingerprint
from citereel.ingest import load_docs


@dataclass(frozen=True)
class RagConfig:
    name: str
    retriever: str = "embedding"
    generator: str = "offline"
    k: int = 3
    provider: str | None = None
    model: str | None = None
    base_url: str | None = None


def run_suite(
    suite: EvalSuite,
    config: RagConfig,
    *,
    out_dir: str | Path | None = None,
) -> SuiteReport:
    """Execute every case under one RAG config; optionally persist each run.json."""
    docs = suite.resolve_docs()
    corpus = load_docs(docs)
    docs_fp = corpus_fingerprint(corpus)
    out: Path | None = Path(out_dir) if out_dir else None
    if out is not None:
        out.mkdir(parents=True, exist_ok=True)

    results: list[CaseResult] = []
    total_ms = 0.0
    for case in suite.cases:
        t0 = time.perf_counter()
        run = ask(
            case.query,
            docs,
            k=config.k,
            retriever=config.retriever,
            generator=config.generator,
            provider=config.provider,
            model=config.model,
            base_url=config.base_url,
        )
        latency = (time.perf_counter() - t0) * 1000
        total_ms += latency
        structure_ok, evidence_ok, gold_ok, failures, kinds = score_case(case, run)
        passed = _passed(case, structure_ok, evidence_ok, gold_ok, run)

        if out is not None:
            run_path = out / f"{config.name}__{case.id}.json"
            run.save(str(run_path))

        results.append(
            CaseResult(
                case_id=case.id,
                query=case.query,
                passed=passed,
                structure_ok=structure_ok,
                evidence_ok=evidence_ok,
                gold_ok=gold_ok,
                latency_ms=round(latency, 2),
                failures=failures,
                failure_kinds=kinds,
                run_id=run.id,
                answer_preview=run.answer[:160],
                config_snapshot=dict(run.meta.get("config") or {}),
            )
        )

    report = SuiteReport(
        suite_id=suite.id,
        config_name=config.name,
        cases=results,
        docs_fingerprint=docs_fp,
        total_latency_ms=round(total_ms, 2),
    )
    if out is not None:
        (out / f"report__{config.name}.json").write_text(
            json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return report


def _passed(case, structure_ok: bool, evidence_ok: bool, gold_ok: bool, run) -> bool:
    if not structure_ok or not gold_ok:
        return False
    if case.expect_evidence_ok is True and not evidence_ok:
        return False
    if case.expect_citations is True and not run.citations:
        return False
    if case.expect_citations is False and run.citations:
        return False
    return True
