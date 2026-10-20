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
        chunks.append(
            f'<section id="cite-{cite.n}" class="cite">'
            f"<h3>[{cite.n}] {source}</h3>"
            f'<p class="chunk-id"><code>{chunk_id}</code></p>'
            f"<pre>{text}</pre>"
            f"</section>"
        )
    steps = _render_steps(run)
    meta = _render_meta(run)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>citereel · {html.escape(run.id)}</title>
  <style>
    body {{ font-family: Georgia, "Times New Roman", serif; max-width: 720px; margin: 2rem auto; padding: 0 1rem; line-height: 1.5; color: #1a1a1a; background: #faf9f7; }}
    h1, h2, h3 {{ font-family: "Segoe UI", system-ui, sans-serif; font-weight: 650; }}
    h1 {{ letter-spacing: -0.02em; }}
    .meta {{ color: #555; font-size: 0.95rem; }}
    .answer {{ background: #fff; border: 1px solid #e6e2da; padding: 1rem 1.1rem; border-radius: 4px; }}
    .cite {{ border-top: 1px solid #ddd; padding: 1rem 0; scroll-margin-top: 1rem; }}
    .cite:target {{ background: #fff6d6; outline: 1px solid #e6d69a; }}
    .chunk-id {{ margin: 0.25rem 0 0.5rem; color: #666; font-size: 0.85rem; }}
    pre {{ white-space: pre-wrap; font-family: ui-monospace, Consolas, monospace; font-size: 0.9rem; }}
    a.cite-ref {{ text-decoration: none; font-weight: 700; color: #0b57d0; }}
    .timeline {{ list-style: none; padding: 0; margin: 0; }}
    .timeline li {{ position: relative; padding: 0.75rem 0 0.75rem 1.4rem; border-left: 2px solid #cfc8bb; margin-left: 0.4rem; }}
    .timeline li::before {{ content: ""; position: absolute; left: -0.4rem; top: 1.05rem; width: 0.65rem; height: 0.65rem; border-radius: 50%; background: #1a1a1a; }}
    .step-type {{ font-family: "Segoe UI", system-ui, sans-serif; font-weight: 650; }}
    .step-ms {{ color: #666; font-size: 0.9rem; }}
    .step-detail {{ margin: 0.35rem 0 0; color: #444; font-size: 0.9rem; }}
    .step-detail code {{ background: #eeeae3; padding: 0.1rem 0.3rem; border-radius: 3px; }}
  </style>
</head>
<body>
  <h1>citereel</h1>
  <p class="meta"><strong>Run</strong> {html.escape(run.id)}{meta}</p>
  <h2>Query</h2>
  <p>{html.escape(run.query)}</p>
  <h2>Answer</h2>
  <div class="answer">{answer}</div>
  <h2>Citations</h2>
  {"".join(chunks) if chunks else "<p>No citations.</p>"}
  <h2>Timeline</h2>
  <ol class="timeline">{steps}</ol>
</body>
</html>
"""


def _render_meta(run: Run) -> str:
    if not run.meta:
        return ""
    parts = []
    for key in ("retriever", "generator", "model"):
        if key in run.meta:
            parts.append(f"{key}={html.escape(str(run.meta[key]))}")
    if not parts:
        return ""
    return " · " + " · ".join(parts)


def _render_steps(run: Run) -> str:
    if not run.steps:
        return "<li><span class='step-type'>none</span></li>"
    items = []
    for index, step in enumerate(run.steps, start=1):
        detail_bits = []
        for key, value in step.detail.items():
            detail_bits.append(f"<code>{html.escape(str(key))}={html.escape(str(value))}</code>")
        detail_html = " ".join(detail_bits)
        items.append(
            f"<li>"
            f"<span class='step-type'>{index}. {html.escape(step.type)}</span> "
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
