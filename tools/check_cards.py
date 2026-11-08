"""Mechanical checks for paper cards and problem cards.

* front matter has the required keys; model_families use the controlled list
* every required section heading is present
* page citations (p. N, pp. N-M, p.N) are within the paper's page count
* every quotation of 6+ words appears verbatim (modulo whitespace,
  punctuation and line-break hyphenation) in the paper's full text

Usage: python3 tools/check_cards.py [CARD_ID ...]
Exit status 1 if any card has an error.
"""

import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / "himcm-modeling"

FAMILIES = {
    "evaluation-mcdm", "statistics-regression", "time-series-forecasting", "differential-equations",
    "compartment-population", "probability-stochastic", "queueing", "simulation-monte-carlo",
    "simulation-agent-cellular", "optimization-math-programming", "optimization-heuristic",
    "graph-network", "machine-learning", "physics-geometry", "economics-cost-benefit",
    "spatial-geographic", "decision-game-theory", "other",
}
PAPER_KEYS = ["id", "year", "problem", "problem_title", "team", "award", "paper_title", "pages",
              "fulltext", "pdf", "model_families", "models", "tools", "deliverables", "data_sources", "tags"]
PAPER_SECTIONS = ["At a glance", "How they read the problem", "Task-by-task approach", "Models and methods",
                  "Data", "Assumptions", "Validation, sensitivity and robustness", "What makes it stand out",
                  "Writing and presentation worth learning", "Notes for reuse"]
PROBLEM_KEYS = ["id", "year", "problem", "title", "statement", "papers", "problem_type"]
PROBLEM_SECTIONS = ["The task in brief", "What makes this problem hard", "How the Outstanding teams approached it",
                    "Common ground", "Different routes that all worked", "Ideas worth borrowing for similar problems"]


def front_matter(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None, text
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            fm[k.strip()] = v.split("  #")[0].strip()
    return fm, text[m.end():]


def parse_list(v):
    v = v.strip()
    if not (v.startswith("[") and v.endswith("]")):
        return None
    return [x.strip().strip('"').strip("'") for x in v[1:-1].split(",") if x.strip()]


def norm(s):
    s = s.replace("-\n", "").replace("­", "")
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s


def words_of(s):
    s = s.replace("-\n", "").replace("\u00ad", "").lower()
    return [w for w in re.split(r"[^a-z0-9]+", s) if w]


def in_order_with_gaps(q, f, max_gap=8):
    """True if word list q occurs in f in order, allowing up to max_gap
    intervening words (table columns, running headers, page breaks)."""
    if not q:
        return True
    for i, w in enumerate(f):
        if w != q[0]:
            continue
        j, k = i, 1
        while k < len(q):
            nxt = next((t for t in range(j + 1, min(j + 2 + max_gap, len(f))) if f[t] == q[k]), None)
            if nxt is None:
                break
            j, k = nxt, k + 1
        if k == len(q):
            return True
    return False


def check_paper(path):
    errs, warns = [], []
    text = path.read_text(encoding="utf-8")
    fm, body = front_matter(text)
    if fm is None:
        return [f"no front matter"], []
    for k in PAPER_KEYS:
        if k not in fm:
            errs.append(f"missing key: {k}")
    fam = parse_list(fm.get("model_families", "[]")) or []
    bad = [f for f in fam if f not in FAMILIES]
    if bad:
        errs.append(f"unknown model_families: {bad}")
    for s in PAPER_SECTIONS:
        if not re.search(rf"^## {re.escape(s)}\s*$", body, re.M):
            errs.append(f"missing section: {s}")
    full = SKILL / "corpus" / "papers" / f"{path.stem}.md"
    if not full.exists():
        return errs + ["no full text"], warns
    ftext = full.read_text(encoding="utf-8")
    npages = len(re.findall(r"^## Page \d+$", ftext, re.M))
    if fm.get("pages") and fm["pages"].isdigit() and int(fm["pages"]) != npages:
        errs.append(f"pages {fm['pages']} != {npages}")
    for m in re.finditer(r"\bpp?\.\s*(\d+)(?:\s*[-–]\s*(\d+))?", body):
        for g in m.groups():
            if g and int(g) > npages:
                errs.append(f"page citation out of range: {m.group(0)} (paper has {npages})")
    nfull = norm(re.sub(r"^## Page \d+$", "", ftext, flags=re.M))
    fwords = words_of(ftext)
    page_texts = re.split(r"^## Page \d+$", ftext, flags=re.M)[1:]
    # Quotations cited to a page: "..." (p. N) or "..." (pp. N-M), straight or curly quotes.
    for m in re.finditer(r"[\"“]([^\"“”\n]{20,400})[\"”][\s,.;:]*\(?\s*pp?\.\s*(\d+)", body):
        q = m.group(1)
        cited = int(m.group(2))
        if 1 <= cited <= len(page_texts) and len(page_texts[cited - 1].split()) < 40:
            warns.append(f"quote from an image-only page (p. {cited}), not machine-checkable: \"{q[:60]}\"")
            continue
        if len(q.split()) < 6:
            continue
        nq = norm(q.replace("…", " ").replace("...", " "))
        if nq in nfull:
            continue
        pieces = [norm(p) for p in re.split(r"\.\.\.|…|\[[^\]]*\]", q) if len(p.split()) >= 4]
        if pieces and all(p in nfull for p in pieces):
            continue
        if in_order_with_gaps(words_of(q), fwords):  # table layout / page break / header
            continue
        errs.append(f"quote not found verbatim: \"{q[:90]}\"")
    words = len(body.split())
    if words < 600:
        warns.append(f"short card ({words} words)")
    return errs, warns


def check_problem(path):
    errs = []
    text = path.read_text(encoding="utf-8")
    fm, body = front_matter(text)
    if fm is None:
        return ["no front matter"], []
    for k in PROBLEM_KEYS:
        if k not in fm:
            errs.append(f"missing key: {k}")
    for s in PROBLEM_SECTIONS:
        if not re.search(rf"^## {re.escape(s)}\s*$", body, re.M):
            errs.append(f"missing section: {s}")
    for pid in parse_list(fm.get("papers", "[]")) or []:
        if not (SKILL / "papers" / f"{pid}.md").exists():
            errs.append(f"listed paper has no card: {pid}")
    return errs, []


def main():
    ids = set(sys.argv[1:])
    failed = 0
    for path in sorted((SKILL / "papers").glob("*.md")) + sorted((SKILL / "problems").glob("*.md")):
        if ids and path.stem not in ids:
            continue
        errs, warns = (check_paper if path.parent.name == "papers" else check_problem)(path)
        if errs or warns:
            print(f"{path.parent.name}/{path.name}")
            for e in errs:
                print("  ERROR", e)
            for w in warns:
                print("  warn ", w)
        failed += bool(errs)
    print(f"checked; {failed} file(s) with errors")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
