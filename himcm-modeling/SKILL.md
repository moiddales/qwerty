---
name: himcm-modeling
description: Knowledge base for the HiMCM (High School Mathematical Contest in Modeling) built from 92 COMAP Outstanding papers, 2014-2024. Use it to read a modeling problem, choose a research direction, plan and carry out the modeling and data analysis, and write, structure and review the paper (summary sheet, sections, figures, memo/letter/article). Includes page-marked full texts of every paper, the official problem statements, per-paper and per-problem analysis cards, and guides.
---

# HiMCM modeling knowledge base

This skill helps a team, or an AI working with a team, do three things well:

1. **Read a problem and choose a direction**: [guides/problem-analysis-and-direction.md](guides/problem-analysis-and-direction.md)
2. **Model and analyze**: [guides/modeling-workflow.md](guides/modeling-workflow.md) and [guides/model-catalog/](guides/model-catalog/README.md)
3. **Write the paper** (the most detailed part): [guides/writing/](guides/writing/README.md), then [guides/review-checklist.md](guides/review-checklist.md)

## Ground rules: read these first

These rules matter more than anything in the guides.

1. **The current problem statement and the current contest rules come first.** Page limits, required parts (summary sheet, table of contents, references, memo, letter, article), file format and dates change from year to year. Papers before 2020 were often longer than 25 pages because the rules were different. Always check the statement and COMAP's current instructions; never infer a rule from a past paper.
2. **The corpus shows what worked, not what is allowed.** These papers show some ways a team reached Outstanding, not the only ways. If no past paper used a method, that says nothing about whether the method fits your problem. Choose methods because they fit the question, the data and the time available, and say why in the paper. The model catalog lists methods outside the corpus for the same reason.
3. **Outstanding does not mean flawless.** Judges reward the overall quality of a paper. Many winning papers contain an unjustified constant, an over-long extrapolation or a formula that does not match the code. Each paper card ends with "Notes for reuse", which flags the few issues that would mislead someone copying the paper. Borrow the ideas, check the details, and never reuse a past paper's numbers without checking their source.
4. **Do not copy text or results.** Learn the techniques and the structure. Write your own words, build your own model and compute your own results. Cite any source you use.
5. **Simple and well-argued beats complex and unexplained.** In this corpus, a clear definition of "best", stated assumptions with reasons, one worked example and honest sensitivity analysis count for more than the number of methods stacked together.
6. **Coverage.** All 92 papers have full texts and analysis cards, and all 22 problems from 2014–2024 represented in the corpus have problem cards (see [catalog.md](catalog.md)). The 2025 statements are included as current references, but there is no 2025 Outstanding-paper corpus in this repository. Read the full texts when a card does not contain the detail you need.

## What is in the knowledge base

| Layer | Path | Use it for | Cost to read |
|---|---|---|---|
| Guides | `guides/` | Methods, workflow, writing advice, checklist | Low |
| Catalog | `catalog.md`, `catalog.json` | Find papers by problem, model family or problem type; see which papers have cards | Low |
| Problem cards | `problems/<YEAR><A/B>.md` | How all Outstanding teams for one problem approached it: common ground, different routes, ideas to borrow | Low |
| Paper cards | `papers/<ID>.md` | One paper: reading of the problem, task-by-task approach, models, data, validation, strengths, writing devices, cautions; all with page citations | Medium |
| Problem statements | `corpus/problems/<YEAR><A/B>.md` | Official text of every problem, 2014-2025, with attachment paths | Low |
| Full texts | `corpus/papers/<ID>.md` | The paper itself, split by `## Page N` markers matching the PDF pages | High |
| Original PDFs | `../sources/papers/<ID>.pdf` (repository root) | Figures, tables, layout, equations that did not extract well | Highest |

Paper ids look like `2021B-11576`: year, problem, team control number. Page citations `(p. N)` in cards and guides refer to page N of that paper's split PDF, which is also the `## Page N` section of its full text.

## How to work efficiently without losing accuracy

Go from cheap to expensive, and stop when you have what you need.

1. Read this file and the guide for the task in front of you.
2. Use `catalog.md` to find relevant problems and papers (same problem, similar problem type, or a model family).
3. Read the problem card, then only the paper cards you need.
4. To check a detail or quote, search the full text (for example `grep -n "sensitivity" corpus/papers/2021B-11576.md`) and read only the pages you need.
5. Open the PDF, or render a page with `python3 tools/render_page.py <ID> <page>` from the repository root, only for figures, tables, page layout or garbled equations. Pages marked "[no extractable text on this page: image only]" (often the memo or article page) can only be read this way.

Never rely on a card for a fact you will put in a paper without checking it in the full text. Cards are summaries written to be accurate, but they are still summaries.

## Typical requests and where to start

| Request | Start with |
|---|---|
| "Here is this year's problem; how should we approach it?" | problem-analysis-and-direction, then the problem cards of similar past problems (catalog: Problem types) |
| "What model should we use for X?" | model-catalog README, then the family file; cite paper cards only as examples |
| "Our model is built; how do we validate it?" | modeling-workflow (validation and sensitivity sections) |
| "Write or improve our summary sheet" | writing/summary-sheet |
| "How should the paper be organized?" | writing/structure-and-sections |
| "Write the memo / letter / news article / app page" | writing/non-technical-deliverables |
| "Review our draft" | review-checklist, then writing/style-and-language |
| "Show me how Outstanding papers did X" | catalog, then cards, then full text pages |

## Adding papers

New papers can be added at any time with `tools/ingest.py`; see `CONTRIBUTING.md` at the repository root. Guides should be updated when new evidence changes or extends a recommendation, not simply because a new paper uses a different method.
