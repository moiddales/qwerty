"""One-off builder for the original 2014-2024 collection (2973-page PDF).

Splits the booklet into one PDF per paper (sources/papers/) and writes the
page-marked full text of each paper (himcm-modeling/corpus/papers/), using
tools/booklet_manifest.json for page ranges, problems and awards.

Usage: python3 tools/split_booklet.py /path/to/booklet.pdf [--only ID ...]

Papers listed in tools/manual_transcriptions/ (scanned papers without a text
layer) take their text from the transcription file instead of pdftotext.
"""

import argparse
import json
import re
import sys
from pathlib import Path

import pypdf.filters
from pypdf import PdfReader, PdfWriter

# The booklet embeds some large images; raise pypdf's default safety limits.
for _name in ("ZLIB_MAX_OUTPUT_LENGTH", "MAX_DECLARED_STREAM_LENGTH", "FLATE_MAX_BUFFER_SIZE",
              "MAX_ARRAY_BASED_STREAM_OUTPUT_LENGTH", "LZW_MAX_OUTPUT_LENGTH", "RUN_LENGTH_MAX_OUTPUT_LENGTH"):
    if hasattr(pypdf.filters, _name):
        setattr(pypdf.filters, _name, 1_000_000_000)

sys.path.insert(0, str(Path(__file__).resolve().parent))

from corpus import CORPUS_PAPERS, REPO, SOURCE_PAPERS, write_fulltext

MANUAL = REPO / "tools" / "manual_transcriptions"


def load_manual(pid: str):
    f = MANUAL / f"{pid}.md"
    if not f.exists():
        return None
    parts = re.split(r"^## Page (\d+)\s*$", f.read_text(encoding="utf-8"), flags=re.M)
    pages = {int(parts[i]): parts[i + 1].strip() for i in range(1, len(parts), 2)}
    return [pages[k] for k in sorted(pages)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("booklet")
    ap.add_argument("--only", nargs="*")
    args = ap.parse_args()
    man = json.loads((REPO / "tools" / "booklet_manifest.json").read_text(encoding="utf-8"))
    reader = PdfReader(args.booklet)
    SOURCE_PAPERS.mkdir(parents=True, exist_ok=True)
    for p in man["papers"]:
        if args.only and p["id"] not in args.only:
            continue
        a, b = p["booklet_pages"]
        out_pdf = SOURCE_PAPERS / f"{p['id']}.pdf"
        w = PdfWriter()
        for i in range(a - 1, b):
            page = reader.pages[i]
            # Link annotations point into the booklet and break pypdf's copy.
            if "/Annots" in page:
                del page["/Annots"]
            w.add_page(page)
        w.compress_identical_objects(remove_duplicates=True, remove_unreferenced=True)
        with open(out_pdf, "wb") as fh:
            w.write(fh)
        meta = dict(p, title=man["problems"][f"{p['year']}{p['problem']}"])
        manual = load_manual(p["id"])
        if manual:
            meta["text_method"] = "manual transcription of page images (scanned paper, no text layer)"
        write_fulltext(meta, out_pdf, CORPUS_PAPERS / f"{p['id']}.md", page_texts=manual)
        print(p["id"], b - a + 1, "pages", "(manual text)" if manual else "")


if __name__ == "__main__":
    main()
