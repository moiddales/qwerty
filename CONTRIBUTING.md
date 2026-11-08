# Contributing: adding papers, cards and guide updates

The knowledge base is designed to grow. New papers can be added at any time, existing uncarded papers can be carded, and guides can be improved as evidence accumulates.

## 1. Add a paper

```bash
python3 tools/ingest.py path/to/paper.pdf --year 2025 --problem A --team 17890 --award "Outstanding"
```

This:

- copies the PDF to `sources/papers/<ID>.pdf`,
- writes the page-marked full text to `himcm-modeling/corpus/papers/<ID>.md`,
- creates a card stub at `himcm-modeling/papers/<ID>.md` if none exists.

Notes:

- `--award` is free text. Record it accurately ("Outstanding", "Finalist", "Meritorious", "Honorable Mention", ...). Lower-award papers are welcome, but their lessons should be used with that in mind.
- If the problem is new to the corpus, add the official statement and attachments under `sources/problems/<YEAR>/` (`<YEAR>_HiMCM_Problem_A.pdf` and so on) and run `python3 tools/build_problem_texts.py`. If an attachment name does not say which problem it belongs to, add it to `ATTACHMENT_PROBLEM` in that script. Pass `--title` to `ingest.py` if no statement is available yet.
- Scanned papers with no text layer: transcribe them into `tools/manual_transcriptions/<ID>.md` using `## Page N` headings, then run `ingest.py` with `--manual`.
- Check the text: open the full text and compare a few pages with the PDF. Glyph problems are fixed in `tools/textclean.py`.

## 2. Write a paper card

Read the whole full text, and look at the PDF for image-only pages (memo, article, app screens) and key figures (`python3 tools/render_page.py <ID> <page>`). Then fill in the stub.

**Front matter**

- `paper_title`: the title on the paper, or "Untitled".
- `model_families`: from the controlled vocabulary in `tools/check_cards.py` (`FAMILIES`). Use `other` and describe it in `models` if nothing fits; propose a new family in a pull request if a family keeps recurring.
- `models`: specific methods, in the paper's own terms where possible.
- `tools`, `deliverables`, `data_sources`, `tags`: short lists.

**Sections** (all required, in this order; aim for about 1,000-1,600 words)

| Section | Content |
|---|---|
| At a glance | One paragraph: the framing, the core model, the main result |
| How they read the problem | How the team interpreted, defined, scoped and decomposed the problem |
| Task-by-task approach | Table: official requirement, their approach, key output, pages |
| Models and methods | The methods and how they were used, with the reasoning |
| Data | Sources, cleaning, gaps and how they were filled |
| Assumptions | Format and representative examples |
| Validation, sensitivity and robustness | What was checked and how |
| What makes it stand out | The strengths worth learning from |
| Writing and presentation worth learning | Summary sheet, paper structure, devices, the non-technical piece, 2-4 short phrasing examples |
| Notes for reuse | 0-3 bullets, only for issues that would mislead someone imitating the paper |

**Principles**

- **Strengths first.** The papers won for good reasons; the card should make those reasons easy to learn. "Notes for reuse" is not a list of every flaw; include only points that would mislead an imitator, phrased as advice.
- **Faithful.** Describe what the paper did, not what it should have done. Cite pages as `(p. N)` or `(pp. N–M)` using PDF page numbers.
- **Quotes are verbatim**, at most about five per card, each one or two sentences, followed by the page citation. The checker verifies them against the full text.
- **No content about AI tools or disclosure statements** in cards or guides.
- **Plain English**, short sentences.

## 3. Write or update a problem card

When all corpus papers for a problem have cards, write `himcm-modeling/problems/<YEAR><A|B>.md` with front matter `id, year, problem, title, statement, papers, problem_type` and the sections: The task in brief; What makes this problem hard; How the Outstanding teams approached it (table with links); Common ground; Different routes that all worked; Ideas worth borrowing for similar problems. See `problems/2020A.md` for an example.

## 4. Check and rebuild

```bash
python3 tools/check_cards.py
```

```bash
python3 tools/build_index.py
```

The checker must report 0 files with errors. Warnings about quotes from image-only pages are expected (those pages can only be checked by eye).

## 5. Update the guides when evidence changes

Guides summarize patterns across papers. Update them when new papers:

- show a new useful technique, structure or device (add it with a citation),
- contradict a recommendation (revise it),
- cover a problem type the guides do not yet discuss.

Do not narrow the guides because new papers happen to use certain methods. The guides must keep the ground rules in `SKILL.md`: the current statement comes first, the corpus shows what worked rather than what is allowed, and methods outside the corpus stay available. Quotes in guides must use the form `"..." (<ID>, p. N)` so the checker can verify them.
