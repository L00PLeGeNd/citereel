from __future__ import annotations

import html
import re

from citereel.models import Run

_CITE_MARK = re.compile(r"\[(\d+)\]")


def render_html(run: Run) -> str:
    """Single-file HTML page: answer marks link to citation anchors."""
    answer = _linkify_citations(run.answer)
    chunks = []
    by_id = run.chunk_by_id()
    for cite in run.citations:
        chunk = by_id.get(cite.chunk_id)
        source = html.escape(chunk.source) if chunk else "?"
        text = html.escape(chunk.text) if chunk else "(missing chunk)"
        chunk_id = html.escape(cite.chunk_id)
        page = ""
        if chunk is not None and chunk.page is not None:
            page = f'<span class="pill">p.{chunk.page}</span>'
        chunks.append(
            f'<section id="cite-{cite.n}" class="cite">'
            f'<div class="cite-head">'
            f'<span class="cite-n">[{cite.n}]</span>'
            f"<h3>{source}</h3>"
            f"{page}"
            f"</div>"
            f'<p class="chunk-id"><code>{chunk_id}</code></p>'
            f'<pre class="chunk-text">{text}</pre>'
            f"</section>"
        )
    steps = _render_steps(run)
    chips = _render_chips(run)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>citereel · {html.escape(run.id)}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Syne:wght@600;700;800&display=swap" rel="stylesheet" />
  <style>
    :root {{
      --ink: #0c1117;
      --panel: #121821;
      --line: #243041;
      --mute: #8b9bb0;
      --text: #e8eef7;
      --accent: #3dffa8;
      --accent-dim: rgba(61, 255, 168, 0.14);
      --warn: #ffc14a;
    }}
    * {{ box-sizing: border-box; }}
    html, body {{ margin: 0; min-height: 100%; }}
    body {{
      font-family: "IBM Plex Mono", ui-monospace, Consolas, monospace;
      color: var(--text);
      background:
        radial-gradient(900px 480px at 12% -8%, rgba(61,255,168,0.12), transparent 55%),
        radial-gradient(700px 420px at 100% 0%, rgba(70,120,255,0.10), transparent 50%),
        linear-gradient(180deg, #0a0e14 0%, var(--ink) 40%, #0a0e14 100%);
      line-height: 1.55;
    }}
    @media (prefers-reduced-motion: no-preference) {{
      body {{ animation: wash 16s ease-in-out infinite alternate; }}
      @keyframes wash {{
        from {{ background-position: 0 0, 0 0, 0 0; }}
        to {{ background-position: 2% 1%, -2% 0, 0 0; }}
      }}
      .shell {{ animation: rise 0.55s ease both; }}
      @keyframes rise {{
        from {{ opacity: 0; transform: translateY(12px); }}
        to {{ opacity: 1; transform: none; }}
      }}
      a.cite-ref {{ transition: background 0.15s ease, color 0.15s ease; }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      * {{ animation: none !important; transition: none !important; }}
    }}
    .shell {{
      max-width: 860px;
      margin: 0 auto;
      padding: 2.2rem 1.25rem 3.5rem;
    }}
    header {{
      display: grid;
      gap: 0.85rem;
      margin-bottom: 1.75rem;
      padding-bottom: 1.35rem;
      border-bottom: 1px solid var(--line);
    }}
    .brand {{
      font-family: Syne, system-ui, sans-serif;
      font-weight: 800;
      font-size: clamp(2.1rem, 5vw, 2.85rem);
      letter-spacing: -0.045em;
      line-height: 1;
      margin: 0;
    }}
    .brand span {{ color: var(--accent); }}
    .tagline {{
      color: var(--mute);
      font-size: 0.92rem;
      max-width: 36rem;
      margin: 0;
    }}
    .chips {{ display: flex; flex-wrap: wrap; gap: 0.45rem; }}
    .pill {{
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      border: 1px solid var(--line);
      background: var(--panel);
      color: var(--mute);
      border-radius: 999px;
      padding: 0.28rem 0.7rem;
      font-size: 0.78rem;
    }}
    .pill strong {{ color: var(--text); font-weight: 600; }}
    .grid {{
      display: grid;
      gap: 1rem;
    }}
    @media (min-width: 840px) {{
      .grid-main {{
        grid-template-columns: 1.15fr 0.85fr;
        align-items: start;
      }}
    }}
    .panel {{
      background: linear-gradient(180deg, rgba(18,24,33,0.95), rgba(14,19,27,0.92));
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 1.05rem 1.15rem 1.2rem;
      box-shadow: 0 24px 60px rgba(0,0,0,0.35);
    }}
    .label {{
      font-family: Syne, system-ui, sans-serif;
      font-size: 0.72rem;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: var(--mute);
      margin: 0 0 0.55rem;
    }}
    .query {{
      font-family: Syne, system-ui, sans-serif;
      font-size: 1.28rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      margin: 0;
    }}
    .answer {{
      font-size: 1.05rem;
      white-space: pre-wrap;
      margin: 0;
    }}
    a.cite-ref {{
      color: var(--ink);
      background: var(--accent);
      border-radius: 0.35rem;
      padding: 0.05rem 0.32rem;
      font-weight: 600;
      text-decoration: none;
      margin: 0 0.1rem;
    }}
    a.cite-ref:hover {{ filter: brightness(1.08); }}
    .cite {{
      padding: 0.85rem 0;
      border-top: 1px solid var(--line);
      scroll-margin-top: 1rem;
    }}
    .cite:first-of-type {{ border-top: 0; padding-top: 0.2rem; }}
    .cite:target, .cite.active {{
      background: var(--accent-dim);
      margin: 0 -0.55rem;
      padding-left: 0.55rem;
      padding-right: 0.55rem;
      border-radius: 10px;
    }}
    .cite-head {{
      display: flex;
      align-items: center;
      gap: 0.55rem;
      flex-wrap: wrap;
    }}
    .cite-n {{
      color: var(--accent);
      font-weight: 600;
    }}
    .cite h3 {{
      font-family: Syne, system-ui, sans-serif;
      font-size: 0.98rem;
      margin: 0;
      font-weight: 700;
    }}
    .chunk-id {{ margin: 0.35rem 0 0.45rem; color: var(--mute); font-size: 0.78rem; }}
    .chunk-text {{
      margin: 0;
      white-space: pre-wrap;
      font-size: 0.86rem;
      color: #c9d4e4;
    }}
    .timeline {{ list-style: none; padding: 0; margin: 0; }}
    .timeline li {{
      position: relative;
      padding: 0.7rem 0 0.7rem 1.15rem;
      border-left: 1px solid var(--line);
      margin-left: 0.35rem;
    }}
    .timeline li::before {{
      content: "";
      position: absolute;
      left: -0.28rem;
      top: 1rem;
      width: 0.5rem;
      height: 0.5rem;
      border-radius: 50%;
      background: var(--accent);
      box-shadow: 0 0 0 3px var(--accent-dim);
    }}
    .step-type {{ font-weight: 600; color: var(--text); }}
    .step-ms {{ color: var(--warn); font-size: 0.82rem; margin-left: 0.35rem; }}
    .step-detail {{ margin: 0.35rem 0 0; color: var(--mute); font-size: 0.78rem; }}
    .step-detail code {{
      display: inline-block;
      margin: 0.15rem 0.25rem 0.15rem 0;
      background: #0a1018;
      border: 1px solid var(--line);
      padding: 0.12rem 0.35rem;
      border-radius: 5px;
      color: #b7c5d8;
    }}
    footer {{
      margin-top: 1.5rem;
      color: var(--mute);
      font-size: 0.78rem;
    }}
  </style>
</head>
<body>
  <div class="shell">
    <header>
      <h1 class="brand">cite<span>reel</span></h1>
      <p class="tagline">Inspect why the model answered that way — citations jump to evidence, timeline shows retrieve → generate.</p>
      <div class="chips">{chips}</div>
    </header>

    <div class="grid grid-main">
      <div class="grid">
        <section class="panel">
          <p class="label">Query</p>
          <p class="query">{html.escape(run.query)}</p>
        </section>
        <section class="panel">
          <p class="label">Answer</p>
          <div class="answer">{answer}</div>
        </section>
        <section class="panel">
          <p class="label">Evidence</p>
          {"".join(chunks) if chunks else "<p class='chunk-id'>No citations.</p>"}
        </section>
      </div>
      <aside class="panel">
        <p class="label">Timeline</p>
        <ol class="timeline">{steps}</ol>
      </aside>
    </div>
    <footer>citereel run · structure map is not semantic proof · use <code>citereel c -E</code> for evidence checks</footer>
  </div>
  <script>
    document.querySelectorAll("a.cite-ref").forEach((a) => {{
      a.addEventListener("click", () => {{
        document.querySelectorAll(".cite").forEach((c) => c.classList.remove("active"));
        const el = document.querySelector(a.getAttribute("href"));
        if (el) el.classList.add("active");
      }});
    }});
  </script>
</body>
</html>
"""


def _render_chips(run: Run) -> str:
    bits = [f'<span class="pill"><strong>run</strong> {html.escape(run.id)}</span>']
    meta = run.meta or {}
    for key in ("retriever", "generator", "model", "provider"):
        if key in meta and meta[key]:
            bits.append(
                f'<span class="pill"><strong>{html.escape(key)}</strong> '
                f"{html.escape(str(meta[key]))}</span>"
            )
    return "".join(bits)


def _render_steps(run: Run) -> str:
    if not run.steps:
        return "<li><span class='step-type'>none</span></li>"
    items = []
    for index, step in enumerate(run.steps, start=1):
        detail_bits = []
        for key, value in step.detail.items():
            detail_bits.append(
                f"<code>{html.escape(str(key))}={html.escape(str(value))}</code>"
            )
        detail_html = " ".join(detail_bits)
        items.append(
            f"<li>"
            f"<span class='step-type'>{index}. {html.escape(step.type)}</span>"
            f"<span class='step-ms'>{step.ms} ms</span>"
            f"<div class='step-detail'>{detail_html}</div>"
            f"</li>"
        )
    return "".join(items)


def _linkify_citations(answer: str) -> str:
    escaped = html.escape(answer)

    def repl(match: re.Match[str]) -> str:
        n = match.group(1)
        return f'<a class="cite-ref" href="#cite-{n}">[{n}]</a>'

    return _CITE_MARK.sub(repl, escaped)
