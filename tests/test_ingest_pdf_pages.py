from pathlib import Path

from citereel.ingest import load_docs


def test_pdf_chunks_preserve_page_numbers(tmp_path: Path, monkeypatch) -> None:
    pdf = tmp_path / "guide.pdf"
    pdf.write_bytes(b"%PDF-1.4 placeholder")

    def fake_pages(_path: Path):
        return [
            (1, "Page one discusses refunds within 14 days."),
            (2, "Page two covers shipping timelines."),
        ]

    monkeypatch.setattr("citereel.ingest._iter_pdf_pages", fake_pages)
    chunks = load_docs(tmp_path)
    assert {c.page for c in chunks} == {1, 2}
    page1 = next(c for c in chunks if c.page == 1)
    assert "refund" in page1.text.lower()
    assert page1.source == "guide.pdf"
    assert page1.id.endswith("#p1") or "#p1#" in page1.id


def test_paragraph_strategy_still_works_on_markdown(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("First para.\n\nSecond para.\n", encoding="utf-8")
    chunks = load_docs(tmp_path)
    assert len(chunks) >= 2
    assert all(c.page is None for c in chunks)
