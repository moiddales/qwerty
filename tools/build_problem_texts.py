"""Build himcm-modeling/corpus/problems/<YEAR><A|B>.md from the official
statements kept in sources/problems/<YEAR>/.

2018 onward: the official PDFs. 2014-2017: the text of COMAP's problem web page
(saved as <YEAR>_HiMCM_Problems_webpage.txt), split into Problem A and B.

Usage: python3 tools/build_problem_texts.py
"""

import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus import REPO, SKILL  # noqa: E402
from textclean import clean_page  # noqa: E402

OUT = SKILL / "corpus" / "problems"
SRC = REPO / "sources" / "problems"
PAGE_URL = "https://www.contest.comap.com/highschool/contests/himcm/{year}problems.html"

MISSING = {
    "2017B": "The attachments (SkiSlopeComparison.xlsx, Wasatch-Peaks-Ranch-Brochure.pdf, "
             "WasatchPeaksTopoMap.pdf) were hosted on mathmodels.org, which no longer resolves; "
             "no archived copy was found.",
    "2020B": "The attachment HiMCM2020ProblemB_ThreatenedPlantsData.xlsx returns 404 on the COMAP site; "
             "no archived copy was found.",
}


def pdf_text(pdf: Path) -> str:
    res = subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True, errors="replace")
    return clean_page(res.stdout)


# Attachments whose file names do not say which problem they belong to.
ATTACHMENT_PROBLEM = {
    "2015_My_City_Crime_Data.xlsx": "B",
    "HiMCM_TriDataSet.xlsx": "A",
    "Sales_Tax_Rate.pdf": "B",
    "COMAP_RollerCoasterData_2018.xlsx": "A",
    "2021_HiMCM_LakeMead_LowHighElevationData.xlsx": "B",
    "2021_HiMCM_LakeMead_MonthlyElevationData.xlsx": "B",
    "2022_HiMCM_Data.xlsx": "B",
    "HiMCM_Olympic_Data.xlsx": "A",
}


def attachments(year: int, letter: str):
    files = []
    for f in sorted((SRC / str(year)).iterdir()):
        n = f.name
        if n.endswith("_webpage.txt") or re.search(r"Problem_[AB]\.pdf$", n):
            continue
        m = re.search(r"Problem_([AB])", n)
        owner = m.group(1) if m else ATTACHMENT_PROBLEM.get(n)
        if owner is None:
            raise SystemExit(f"attachment {n}: add it to ATTACHMENT_PROBLEM")
        if owner != letter:
            continue
        files.append(f"sources/problems/{year}/{n}")
    return files


def write(pid: str, year: int, letter: str, title: str, text: str, source: str, papers: int):
    att = attachments(year, letter)
    lines = [
        "---",
        f"id: {pid}",
        f"year: {year}",
        f"problem: {letter}",
        f"title: \"{title}\"",
        f"source: {source}",
        f"official_page: {PAGE_URL.format(year=year)}",
        f"papers_in_corpus: {papers}",
        "---",
        "",
        f"# {year} HiMCM Problem {letter}: {title} - official statement",
        "",
    ]
    if att:
        lines += ["Attachments (repository paths): " + ", ".join(f"`{a}`" for a in att), ""]
    if pid in MISSING:
        lines += ["Missing attachments: " + MISSING[pid], ""]
    if papers == 0:
        lines += ["No papers for this problem are in the corpus.", ""]
    lines += ["---", "", text.strip(), ""]
    (OUT / f"{pid}.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    man = json.loads((REPO / "tools" / "booklet_manifest.json").read_text(encoding="utf-8"))
    titles = dict(man["problems"])
    counts = {}
    for p in man["papers"]:
        k = f"{p['year']}{p['problem']}"
        counts[k] = counts.get(k, 0) + 1
    for year in sorted(int(d.name) for d in SRC.iterdir() if d.name.isdigit()):
        web = SRC / str(year) / f"{year}_HiMCM_Problems_webpage.txt"
        if web.exists():
            raw = web.read_text(encoding="utf-8")
            parts = re.split(r"^\s*Problem B\s*$", raw, maxsplit=1, flags=re.M)
            texts = {"A": re.sub(r"^\s*Problem A\s*$", "", parts[0], count=1, flags=re.M), "B": parts[1]}
            for L in "AB":
                body = "\n".join(l.strip() for l in texts[L].splitlines())
                body = re.sub(r"\n{3,}", "\n\n", body)
                pid = f"{year}{L}"
                write(pid, year, L, titles[pid], body, f"sources/problems/{year}/{web.name}", counts.get(pid, 0))
        else:
            for L in "AB":
                pdf = SRC / str(year) / f"{year}_HiMCM_Problem_{L}.pdf"
                text = pdf_text(pdf)
                pid = f"{year}{L}"
                title = titles.get(pid)
                if title is None:  # problems with no papers in the corpus
                    m = re.search(rf"Problem {L}:\s*(.+)", text)
                    title = m.group(1).strip() if m else f"Problem {L}"
                write(pid, year, L, title, text, f"sources/problems/{year}/{pdf.name}", counts.get(pid, 0))
                print(pid, title)


if __name__ == "__main__":
    main()
