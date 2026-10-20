# citereel

**A developer tool for understanding *why* a RAG system answered that way — and what changed after you tweak it.**

Not another knowledge-base chatbot. CiteReel records retrieval → generation → citations as an inspectable run, checks whether evidence actually supports each claim, and lets you compare configs on a fixed eval suite so results stay reproducible.

[![ci](https://github.com/L00PLeGeNd/citereel/actions/workflows/ci.yml/badge.svg)](https://github.com/L00PLeGeNd/citereel/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/citereel.svg)](https://pypi.org/project/citereel/)

<p align="center"><em>Real offline demo run — branded inspect view with clickable <code>[n]</code>, evidence chunks, and retrieve → generate timeline.</em></p>
## Why it exists

When you change a retriever, prompt, model, or chunking strategy, you need more than “the answer looks better.” CiteReel helps you answer:

| Question | How CiteReel helps |
|---|---|
| What evidence did this answer cite? | Run record maps `[n]` → chunk text |
| Does that evidence *really* support each claim? | Structure check **plus** semantic evidence eval (`check -E`) |
| Did quality get better or worse after a change? | Fixed eval suite + config comparison report |
| Was the failure retrieval, generation, chunking, or citation mapping? | Failure kinds on each eval case |
| Can someone else reproduce my conclusion? | Same suite JSON + saved runs + config / docs fingerprints |

> **Important:** a correct citation *format* does not mean a correct answer. Structure validation only proves mapping integrity. Semantic support is a separate check — and still an assist signal for human review, not a proof of truth.

## Workflow

```mermaid
flowchart LR
  A[Fixed eval suite<br/>queries · gold · expectations] --> B[Run RAG config<br/>retriever · chunking · model]
  B --> C[Record run.json<br/>citations · steps · config]
  C --> D[Validate<br/>structure + evidence]
  D --> E[Compare configs<br/>pass/fail · latency · regressions]
  E --> F[Reproduce<br/>same suite · same fingerprints]
```

| Layer | Today | Value you get |
|---|---|---|
| Retrieval | keyword, embedding | Score hit/miss against gold evidence tokens |
| Generation | offline + OpenAI-compatible | Compare answer quality/stability across configs |
| Citations | structure map + integrity | Evidence eval: support / refute / insufficient |
| Records | JSON runs | Config snapshot, docs fingerprint, schema version |
| Diff / eval | answer · cites · retrieved | Reproducible suite reports and regressions |

## Quick start

```bash
pip install citereel
# optional: pip install "citereel[llm]" "citereel[gui]"
```

```bash
# Interactive demo (writes examples/sample_run.json when run from a checkout)
citereel d -g offline
citereel s 1              # jump to citation [1]
citereel h                # HTML with clickable cites
citereel c -E             # structure + semantic evidence

# Fixed-suite eval (bundled demo-refund, no API key)
citereel e -n offline-emb -o ./eval_out

# Change one knob, compare
citereel e -n offline-kw -R keyword -o ./eval_out2 \
  -A ./eval_out/report__offline-emb.json
```

Ask your own docs:

```bash
citereel a "What is the refund window?" -d ./my_docs -g offline -o run.json
citereel c run.json -E
citereel df run_a.json run_b.json
```

Desktop shell: `citereel g` (install `citereel[gui]` for a native window; otherwise opens the browser).

## Who it is for

- **RAG developers** — debug weak retrieval, missing cites, or silent answer drift  
- **AI app builders** — leave comparable run records when swapping models / prompts / retrievers  
- **Learners & researchers** — see how chunking, retrieve, generate, cite, and eval connect  
- **OSS contributors** — a small Python surface for CLI, modules, tests, and CI around AI engineering  

MIT licensed. Using an online model may incur *provider* fees; CiteReel itself is free and open source.

## What it is / is not

**Is**

- A **run recorder + citation inspector + eval/compare harness** for local (or API-backed) RAG  
- Early-stage **engineering tooling**, with a full basic loop: retrieve → generate → record → check → replay → diff/eval  

**Is not**

- A hosted knowledge-base / chat product with accounts, billing tiers, or a managed corpus UI  
- An enterprise “evaluation platform” with dashboards, RBAC, or guaranteed semantic entailment  
- A replacement for human judgment — evidence checks are heuristics to *surface* bad cites, not certify truth  

Long-term value hangs on three questions we keep optimizing for:

1. Can we reliably tell whether an answer is actually supported by evidence?  
2. Can we fairly compare RAG configs on a fixed suite?  
3. Can another developer reproduce and verify a result?

## Eval suite (minimal shape)

```json
{
  "id": "my-suite",
  "docs": "./my_docs",
  "cases": [
    {
      "id": "refund-window",
      "query": "What is the refund window?",
      "gold_answer_contains": ["14"],
      "gold_evidence_contains": ["14"],
      "expect_citations": true,
      "expect_evidence_ok": true
    }
  ]
}
```

```bash
citereel e path/to/suite.json -n my-config -g offline -o ./out
```

## License

MIT