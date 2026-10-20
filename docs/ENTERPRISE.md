# Enterprise use: what citereel is (and is not)

## Verdict

**Suitable for production assistance (human-in-the-loop), not as an unattended production answer service.**

Use it when a person needs a **recorded, citable, replayable** answer over local docs (policy, handbook, runbooks). Do **not** wire it as the sole automated decision path for billing, access control, medical, or legal outcomes without additional review systems.

## Fits

- Analyst / support / eng **assist**: ask → cited answer → click `[n]` → verify chunk
- Audit trail: `run.json` + `citereel check` + HTML export
- Offline or OpenAI-compatible LLM backends with citation sanitization

## Does not fit (yet)

- Multi-tenant SaaS, SSO, RBAC, network isolation as a product
- Guaranteed semantic retrieval over huge corpora (default hashing is local/fast, not enterprise IR)
- SLA-backed hosted inference
- Automatic red-team / jailbreak resistance beyond citation stripping

## Assist hardening already in the CLI

| Control | How |
|---------|-----|
| Citation integrity | `citereel check run.json` / `ask --strict` |
| Retrieved content fingerprint | `meta.retrieved_sha256` |
| Corpus size caps | `CITEREEL_MAX_FILES`, `CITEREEL_MAX_CHUNK_CHARS`, `CITEREEL_MAX_TOTAL_CHARS` |
| LLM timeout / retry | `CITEREEL_LLM_TIMEOUT`, `CITEREEL_LLM_RETRIES` |
| Secret-ish warnings | flagged in `check` |

## Recommended enterprise-assist setup

```bash
pip install -e ".[llm]"
# Prefer real semantic retrieval for larger corpora:
# pip install -e ".[llm,embed]"
# set CITEREEL_EMBEDDER=st

citereel ask "..." --docs /secure/docs --generator openai --provider deepseek --strict -o run.json
citereel check run.json
citereel show 1 run.json
```

Keep API keys in the environment (or a secret manager). Never commit `run.json` that contains confidential passages to a public remote unless policy allows.
