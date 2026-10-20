from citereel.html import render_html
from citereel.pipeline import ask

from citereel.paths import DEMO_DOCS

DOCS = DEMO_DOCS


def test_html_links_answer_marks_to_chunk_anchors() -> None:
    run = ask("What is the refund window?", DOCS, k=3, generator="offline")
    page = render_html(run)
    assert 'id="cite-1"' in page
    assert 'href="#cite-1"' in page
    assert run.query in page
    assert run.retrieved[0].source in page
    assert 'class="timeline"' in page
    assert "retrieve" in page
    assert "generate" in page
