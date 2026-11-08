# HiMCM Modeling Knowledge Base

A knowledge base for the **HiMCM (High School Mathematical Contest in Modeling)**, built from 92 COMAP **Outstanding** papers from 2014 to 2024, used with the authors' authorization. It is written for both people and AI assistants. It helps with three things:

1. **Reading a problem and choosing a research direction.**
2. **Modeling and data analysis**: workflow, validation, sensitivity, and a catalog of methods.
3. **Writing the paper**: summary sheet, structure, figures, style, and the memo, letter, article or app page.

## Start here

- **People**: read [himcm-modeling/SKILL.md](himcm-modeling/SKILL.md) (ground rules and a map of the knowledge base), then the guide you need:
  - [Reading the problem and choosing a direction](himcm-modeling/guides/problem-analysis-and-direction.md)
  - [Modeling and data analysis workflow](himcm-modeling/guides/modeling-workflow.md)
  - [Model catalog](himcm-modeling/guides/model-catalog/README.md)
  - [Writing the paper](himcm-modeling/guides/writing/README.md)
  - [Review checklist](himcm-modeling/guides/review-checklist.md)
- **AI assistants**: load `himcm-modeling/` as a skill. `SKILL.md` has the front matter, the ground rules and the reading order that keeps cost low without losing accuracy.
- **Looking for examples**: [himcm-modeling/catalog.md](himcm-modeling/catalog.md) lists every paper and problem, with links to analysis cards, full texts and official statements.

## How to read the papers' lessons

The papers are evidence of what worked, not rules. A method that no past paper used may still be the right one, and Outstanding papers contain mistakes. Each card ends with "Notes for reuse" that flag the few points that would mislead someone imitating the paper. The current year's problem statement and contest rules always take priority over anything here.

## Repository layout

```
himcm-modeling/              the skill
  SKILL.md                   entry point: ground rules, map, reading order
  guides/                    direction, workflow, model catalog, writing, checklist
  problems/<YEAR><A|B>.md    problem cards: how the Outstanding teams approached one problem
  papers/<ID>.md             paper cards: one paper's approach, strengths, writing, with page citations
  corpus/problems/           official problem statements 2014-2025 (text)
  corpus/papers/<ID>.md      full text of every paper, split by "## Page N" markers
  catalog.md, catalog.json   generated index
sources/
  papers/<ID>.pdf            the original papers, one PDF each
  problems/<YEAR>/           official statements, data files and attachments
  problems/contest-materials summary sheet template
  results/                   COMAP results documents 2014-2025
tools/                       scripts to build, extend and check the knowledge base
```

Paper ids have the form `<YEAR><PROBLEM>-<TEAM>`, for example `2021B-11576`. A page citation `(p. N)` refers to page N of that paper's PDF in `sources/papers/`, which is also the `## Page N` section of its full text.

## Status

- Full texts and PDFs: all 92 papers. Official statements: all problems 2014-2025 (attachments for 2017B and 2020B could not be recovered; see their statement files).
- Analysis cards: 33 paper cards and 6 problem cards (2018A, 2020A, 2021A, 2021B, 2023A, 2024B). The other papers can be read in full text and carded later; see [CONTRIBUTING.md](CONTRIBUTING.md).
- The guides are built mainly from the carded papers.

## Tools

Run from the repository root (Python 3; `pdftotext` and `pdftoppm` from poppler; `pypdf` for splitting):

| Command | Purpose |
|---|---|
| `python3 tools/check_cards.py` | Check cards and guides: required fields and sections, page ranges, verbatim quotes against the full texts, paper ids, links |
| `python3 tools/build_index.py` | Regenerate `catalog.md` and `catalog.json` |
| `python3 tools/ingest.py paper.pdf --year Y --problem A --team N --award "..."` | Add a new paper (PDF, full text, card stub) |
| `python3 tools/render_page.py <ID> <page>` | Render a PDF page to an image (figures, memo pages, garbled equations) |
| `python3 tools/build_problem_texts.py` | Rebuild problem statement texts from `sources/problems/` |
| `python3 tools/split_booklet.py booklet.pdf` | Rebuild the 92 papers from the original booklet (one-time) |

## Rights

The papers are included with the authorization of their authors for use by this organization. Problem statements and results documents are COMAP materials. Keep the repository private unless the rights holders agree otherwise.
