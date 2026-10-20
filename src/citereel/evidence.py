"""Semantic evidence evaluation: citation structure ≠ claim support.

Offline heuristics catch clear contradictions (e.g. wrong numbers) and weak
overlap. This is an assist signal for human review, not a guarantee.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from citereel.models import Chunk, Run

_CITE = re.compile(r"\[(\d+)\]")
_SENTENCE = re.compile(r"(?<=[.!?])\s+|\n+")
_NUMBER = re.compile(r"\d+(?:\.\d+)?")
_TOKEN = re.compile(r"[a-z0-9]+", re.I)
_STOP = frozenset(
    "a an the is are was were be been being of to in for on with and or but "
    "that this these those it its as at by from within may can should would "
    "customers customer request requests available".split()
)


@dataclass(frozen=True)
class ClaimJudgement:
    claim: str
    citation_n: int
    chunk_id: str
    verdict: str  # support | refute | insufficient
    rationale: str


@dataclass
class EvidenceReport:
    ok: bool
    judgements: list[ClaimJudgement] = field(default_factory=list)

    @property
    def errors(self) -> list[str]:
        out: list[str] = []
        for j in self.judgements:
            if j.verdict == "support":
                continue
            out.append(f"[{j.citation_n}] {j.verdict}: {j.claim!r} ({j.rationale})")
        return out


def evaluate_evidence(run: Run) -> EvidenceReport:
    """Judge each cited claim against its linked chunk text."""
    by_id = run.chunk_by_id()
    cite_to_chunk = {c.n: c.chunk_id for c in run.citations}
    judgements: list[ClaimJudgement] = []

    for claim, ns in _claims_with_cites(run.answer):
        for n in ns:
            chunk_id = cite_to_chunk.get(n)
            if not chunk_id or chunk_id not in by_id:
                judgements.append(
                    ClaimJudgement(
                        claim=claim,
                        citation_n=n,
                        chunk_id=chunk_id or "",
                        verdict="insufficient",
                        rationale="citation does not resolve to a retrieved chunk",
                    )
                )
                continue
            judgements.append(_judge(claim, n, by_id[chunk_id]))

    bad = [j for j in judgements if j.verdict != "support"]
    return EvidenceReport(ok=not bad, judgements=judgements)


def _claims_with_cites(answer: str) -> list[tuple[str, list[int]]]:
    parts = [p.strip() for p in _SENTENCE.split(answer) if p and p.strip()]
    if not parts:
        parts = [answer.strip()] if answer.strip() else []
    out: list[tuple[str, list[int]]] = []
    for part in parts:
        ns = [int(m.group(1)) for m in _CITE.finditer(part)]
        if not ns:
            continue
        claim = _CITE.sub("", part).strip(" ,;:-")
        if claim:
            out.append((claim, sorted(set(ns))))
    return out


def _judge(claim: str, n: int, chunk: Chunk) -> ClaimJudgement:
    evidence = chunk.text
    claim_nums = set(_NUMBER.findall(claim))
    evid_nums = set(_NUMBER.findall(evidence))
    conflicting = claim_nums - evid_nums
    if claim_nums and evid_nums and conflicting:
        return ClaimJudgement(
            claim=claim,
            citation_n=n,
            chunk_id=chunk.id,
            verdict="refute",
            rationale=(
                f"claim numbers {sorted(conflicting)} not in cited passage "
                f"(passage has {sorted(evid_nums)})"
            ),
        )

    claim_toks = _content_tokens(claim)
    evid_toks = _content_tokens(evidence)
    if not claim_toks:
        return ClaimJudgement(
            claim=claim,
            citation_n=n,
            chunk_id=chunk.id,
            verdict="insufficient",
            rationale="empty claim after stripping citations",
        )
    overlap = claim_toks & evid_toks
    ratio = len(overlap) / len(claim_toks)
    if ratio >= 0.4 or (claim_nums and claim_nums <= evid_nums):
        return ClaimJudgement(
            claim=claim,
            citation_n=n,
            chunk_id=chunk.id,
            verdict="support",
            rationale=f"lexical overlap {ratio:.2f}",
        )
    return ClaimJudgement(
        claim=claim,
        citation_n=n,
        chunk_id=chunk.id,
        verdict="insufficient",
        rationale=f"weak overlap {ratio:.2f}; passage does not clearly support claim",
    )


def _content_tokens(text: str) -> set[str]:
    return {t.lower() for t in _TOKEN.findall(text) if t.lower() not in _STOP and len(t) > 1}
