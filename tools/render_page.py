"""Render pages of a paper PDF to PNG so a person or an AI can look at
figures, tables and equations that do not survive text extraction.

Usage:
    python3 tools/render_page.py 2024A-14995 11            # one page
    python3 tools/render_page.py 2024A-14995 11-13 --dpi 150 --out /tmp/pages

Page numbers are the `## Page N` numbers used in corpus/papers/<id>.md.
Requires pdftoppm (poppler-utils).
"""

import argparse
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paper_id", help="e.g. 2024A-14995")
    ap.add_argument("pages", help="N or N-M")
    ap.add_argument("--dpi", type=int, default=120)
    ap.add_argument("--out", default="rendered_pages", help="output directory (created if missing)")
    args = ap.parse_args()
    pdf = REPO / "sources" / "papers" / f"{args.paper_id}.pdf"
    if not pdf.exists():
        raise SystemExit(f"no such paper PDF: {pdf}")
    first, _, last = args.pages.partition("-")
    last = last or first
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    prefix = out / f"{args.paper_id}-p"
    subprocess.run(["pdftoppm", "-r", str(args.dpi), "-f", first, "-l", last, "-png", str(pdf), str(prefix)], check=True)
    for f in sorted(out.glob(f"{args.paper_id}-p*.png")):
        print(f)


if __name__ == "__main__":
    main()
