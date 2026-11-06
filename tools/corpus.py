"""Shared helpers for building the corpus: per-page text extraction and the
full-text Markdown format used under himcm-modeling/corpus/papers/."""

import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from textclean import clean_page  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / "himcm-modeling"
CORPUS_PAPERS = SKILL / "corpus" / "papers"
SOURCE_PAPERS = REPO / "sources" / "papers"

if shutil.which("pdftotext") is None:
    raise SystemExit("pdftotext (poppler-utils) is required. Install poppler-utils and poppler-data.")


def extract_page(pdf: Path, page: int) -> str:
    """Raw `pdftotext -layout` output for one page (1-based)."""
    res = subprocess.run(
        ["pdftotext", "-layout", "-f", str(page), "-l", str(page), str(pdf), "-"],
        capture_output=True, text=True, errors="replace",
    )
    return res.stdout


def page_count(pdf: Path) -> int:
    res = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, errors="replace")
    for line in res.stdout.splitlines():
        if line.startswith("Pages:"):
            return int(line.split()[1])
    raise ValueError(f"cannot read page count of {pdf}")


def write_fulltext(meta: dict, pdf: Path, out: Path, page_texts=None) -> None:
    """Write the page-marked full text of one paper.

    meta needs: id, year, problem, team, award, title (problem title).
    page_texts: optional list of already-cleaned page strings (e.g. a manual
    transcription for scanned papers); otherwise text is extracted from pdf.
    """
    n = page_count(pdf)
    if page_texts is None:
        page_texts = [clean_page(extract_page(pdf, i)) for i in range(1, n + 1)]
    assert len(page_texts) == n, f"{meta['id']}: {len(page_texts)} texts for {n} pages"
    rel_pdf = Path("sources/papers") / pdf.name
    head = [
        "---",
        f"id: {meta['id']}",
        f"year: {meta['year']}",
        f"problem: {meta['problem']}",
        f"problem_title: \"{meta['title']}\"",
        f"team: {meta['team']}",
        f"award: {meta['award']}",
        f"pages: {n}",
        f"pdf: {rel_pdf.as_posix()}  # path from the repository root",
        f"text: {meta.get('text_method', 'pdftotext -layout, cleaned by tools/textclean.py')}",
        "---",
        "",
        f"# {meta['year']} HiMCM Problem {meta['problem']} ({meta['title']}) - Team {meta['team']} - full text",
        "",
        "Page numbers are pages of the paper PDF (page 1 = first page of the submission).",
        "Equations, tables and figures can be garbled or missing in text form; U+FFFD marks a lost glyph.",
        "Open the PDF page (or run tools/render_page.py) when exact notation or a figure matters.",
        "",
    ]
    body = []
    for i, t in enumerate(page_texts, 1):
        body.append(f"## Page {i}\n")
        body.append(t if t.strip() else "[no extractable text on this page: image only]")
        body.append("")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(head + body) + "\n", encoding="utf-8")
