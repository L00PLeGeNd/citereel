# CiteReel usage guide

Short commands work the same on PowerShell, cmd, bash, and zsh:

| Short | Full | Purpose |
|-------|------|---------|
| `a` | `ask` | Run RAG over docs → `run.json` |
| `d` | `demo` | Bundled refund-window demo |
| `s` | `show` | Jump to citation `[n]` |
| `h` | `html` | Single-file HTML inspect page |
| `c` | `check` | Validate structure (`-E` = evidence) |
| `r` | `replay` | Replay a run offline |
| `df` | `diff` | Compare two runs |
| `e` | `eval` | Fixed suite + optional compare |
| `g` | `gui` | Desktop / browser shell |
| `p` | `providers` | List OpenAI-compatible presets |

Run `citereel --help` or `citereel <cmd> --help` for flags.

---

## 1. Install

```bash
pip install citereel

# optional extras
pip install "citereel[llm]"   # OpenAI-compatible generators
pip install "citereel[gui]"   # native window shell
```

From a git checkout:

```bash
pip install -e ".[llm,gui]"
```

---

## 2. Five-minute demo (no API key)

```bash
citereel d -g offline          # write sample run (examples/ or cwd)
citereel s 1                   # show chunk behind [1]
citereel h                     # HTML with clickable cites
citereel c -E                  # structure + semantic evidence check
```

Open the HTML file in a browser. Click `[1]` to jump to the evidence chunk; the timeline shows retrieve → generate.

---

## 3. Ask your own docs

Put `.md` / `.txt` / `.pdf` files in a folder, then:

```bash
citereel a "What is the refund window?" -d ./my_docs -g offline -o run.json
citereel s 1 run.json
citereel h run.json -o run.html
citereel c run.json -E
```

Useful ask flags:

| Flag | Meaning |
|------|---------|
| `-d` / `--docs` | Docs folder |
| `-o` / `--out` | Output `run.json` path |
| `-R` / `--retriever` | `embedding` (default) or `keyword` |
| `-g` / `--generator` | `auto` \| `offline` \| `openai` |
| `-k` | Top-k chunks |
| `-S` / `--strict` | Fail if citation structure is broken |
| `-V` / `--verbose` | Print step details |

---

## 4. Online / OpenAI-compatible models

```bash
pip install "citereel[llm]"
citereel p                     # list presets (DeepSeek, OpenAI, …)

# example: DeepSeek via preset
set OPENAI_API_KEY=sk-...      # PowerShell: $env:OPENAI_API_KEY="sk-..."
citereel a "..." -d ./my_docs -g openai -P deepseek -o run.json -S
```

Or pass `--base-url` / `--model` for any OpenAI-compatible endpoint.

---

## 5. Inspect, replay, diff

```bash
citereel vw run.json           # pretty-print run + citation map
citereel r run.json            # replay offline (no LLM call)
citereel df run_a.json run_b.json
```

Diff highlights answer, citations, and retrieved chunk changes between two recorded runs.

---

## 6. Eval suite (compare configs)

Minimal suite JSON:

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
# bundled demo suite (no path needed)
citereel e -n offline-emb -g offline -o ./eval_out

# your suite
citereel e path/to/suite.json -n my-config -g offline -o ./out

# change one knob, compare to a prior report
citereel e path/to/suite.json -n offline-kw -R keyword -o ./out2 \
  -A ./out/report__my-config.json
```

Each case writes a run under `-o`; the report JSON is what `-A` compares against.

---

## 7. GUI

```bash
pip install "citereel[gui]"
citereel g
# or: citereel g --host 127.0.0.1 --port 8765
```

Without the GUI extra, CiteReel falls back to opening the browser.

---

## 8. What “check” means

| Mode | Command | Checks |
|------|---------|--------|
| Structure | `citereel c run.json` | `[n]` maps to real chunks; no dangling cites |
| Evidence | `citereel c run.json -E` | Heuristic support / refute / insufficient per claim |

Structure OK ≠ answer correct. Evidence is an **assist signal for human review**, not a proof of truth.

---

## Related

- [README](../README.md) — product positioning and boundaries  
- [ENTERPRISE.md](ENTERPRISE.md) — when it fits (and does not) for assist workflows  
