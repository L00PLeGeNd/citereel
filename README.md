# citereel

**Verifiable, comparable, reproducible RAG run records.**

Not another knowledge-base UI — a workflow for developers who need to answer:

- What evidence does this answer cite?
- Does that evidence actually support each claim?
- After changing retriever / chunking / model, did quality get better or worse?
- Was the failure in retrieval, generation, chunking, or citation mapping?
- Can someone else reproduce the result on the same fixed suite?

[![ci](https://github.com/L00PLeGeNd/citereel/actions/workflows/ci.yml/badge.svg)](https://github.com/L00PLeGeNd/citereel/actions/workflows/ci.yml)

## Install

```bash
pip install citereel
pip install "citereel[llm]"     # DeepSeek / OpenAI-compatible
pip install "citereel[gui]"     # desktop window shell
```

## Core loop

```bash
# 1) Fixed eval suite (bundled demo, or your own JSON)
citereel e -n offline-emb -o ./eval_out

# 2) Try another config and compare
citereel e -n offline-kw -R keyword -o ./eval_out2 \
  -A ./eval_out/report__offline-emb.json

# 3) Inspect one run: citations + evidence
citereel s 1 path/to/run.json
citereel c path/to/run.json -E
```

Also: `citereel g` GUI · `citereel d` demo · `citereel a "…" -d ./docs` · `citereel df a.json b.json`

## Eval suite shape

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

## License

MIT
