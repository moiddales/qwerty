"""Add a new paper to the knowledge base.

Copies the PDF to sources/papers/<ID>.pdf, writes the page-marked full text to
himcm-modeling/corpus/papers/<ID>.md and, if it does not exist yet, a paper
card stub at himcm-modeling/papers/<ID>.md to be filled in (see CONTRIBUTING.md).

Usage:
    python3 tools/ingest.py path/to/paper.pdf --year 2025 --problem A --team 17890 \
        --award "Outstanding" [--title "Official problem title"]

ID format: <YEAR><PROBLEM>-<TEAM>, e.g. 2025A-17890. --award is free text such as
"Outstanding", "Finalist", "Meritorious", "Honorable Mention", "Successful Participant",
or "Unknown". The award is recorded so guides can weigh evidence appropriately.

For a scanned paper with no text layer, transcribe it into
tools/manual_transcriptions/<ID>.md (sections '## Page N') and pass --manual.
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus import CORPUS_PAPERS, REPO, SKILL, SOURCE_PAPERS, write_fulltext  # noqa: E402

STUB = """---
id: {id}
year: {year}
problem: {problem}
problem_title: "{title}"
team: {team}
award: {award}
paper_title: "TODO"
pages: {pages}
fulltext: corpus/papers/{id}.md
pdf: sources/papers/{id}.pdf   # repository-root path
model_families: []
models: []
tools: []
deliverables: []
data_sources: []
tags: []
---

# {id}: TODO paper title

<!-- Fill in every section following the template in CONTRIBUTING.md. -->

## At a glance

## How they read the problem

## Task-by-task approach
| Official requirement | Their approach | Key output / result | Pages |
|---|---|---|---|

## Models and methods

## Data

## Assumptions

## Validation, sensitivity and robustness

## What makes it stand out

## Writing and presentation worth learning

## Notes for reuse
"""


def problem_title(year: int, problem: str):
    f = SKILL / "corpus" / "problems" / f"{year}{problem}.md"
    if f.exists():
        m = re.search(r'^title: "(.*)"$', f.read_text(encoding="utf-8"), re.M)
        if m:
            return m.group(1)
    man = json.loads((REPO / "tools" / "booklet_manifest.json").read_text(encoding="utf-8"))
    return man["problems"].get(f"{year}{problem}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--problem", required=True, choices=["A", "B", "C"])
    ap.add_argument("--team", required=True)
    ap.add_argument("--award", default="Unknown")
    ap.add_argument("--title", help="official problem title (needed if the problem is new to the corpus)")
    ap.add_argument("--manual", action="store_true", help="use tools/manual_transcriptions/<ID>.md as the text")
    args = ap.parse_args()

    pid = f"{args.year}{args.problem}-{args.team}"
    title = args.title or problem_title(args.year, args.problem)
    if not title:
        raise SystemExit("Unknown problem: pass --title and add the official statement (see CONTRIBUTING.md).")
    SOURCE_PAPERS.mkdir(parents=True, exist_ok=True)
    dest = SOURCE_PAPERS / f"{pid}.pdf"
    shutil.copyfile(args.pdf, dest)

    page_texts = None
    meta = {"id": pid, "year": args.year, "problem": args.problem, "team": args.team,
            "award": args.award, "title": title}
    if args.manual:
        f = REPO / "tools" / "manual_transcriptions" / f"{pid}.md"
        parts = re.split(r"^## Page (\d+)\s*$", f.read_text(encoding="utf-8"), flags=re.M)
        page_texts = [parts[i + 1].strip() for i in range(1, len(parts), 2)]
        meta["text_method"] = "manual transcription of page images (scanned paper, no text layer)"
    write_fulltext(meta, dest, CORPUS_PAPERS / f"{pid}.md", page_texts=page_texts)

    card = SKILL / "papers" / f"{pid}.md"
    if not card.exists():
        pages = len(re.findall(r"^## Page \d+$", (CORPUS_PAPERS / f"{pid}.md").read_text(encoding="utf-8"), re.M))
        card.write_text(STUB.format(id=pid, year=args.year, problem=args.problem, title=title,
                                    team=args.team, award=args.award, pages=pages), encoding="utf-8")
    print(f"ingested {pid}: {dest.relative_to(REPO)}, corpus/papers/{pid}.md, papers/{pid}.md")
    print("Next: fill in the card, update or create problems/<YEAR><P>.md, then run tools/build_index.py")


if __name__ == "__main__":
    main()
