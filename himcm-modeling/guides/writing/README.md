# Writing the paper

Writing is where many good models lose their value. Judges read many papers in a short time. They meet your summary sheet first, then look for each requirement's answer, then judge whether the reasoning holds up. A paper that makes all this easy is read generously; one that hides its answers is not.

This folder is the most detailed part of the knowledge base:

| File | Covers |
|---|---|
| [summary-sheet.md](summary-sheet.md) | The one-page summary: what it must do, structures that worked, phrasing |
| [structure-and-sections.md](structure-and-sections.md) | Overall organization and what goes in each section, from the introduction to the appendix |
| [figures-tables-equations.md](figures-tables-equations.md) | Visual devices, tables, equations, worked examples |
| [non-technical-deliverables.md](non-technical-deliverables.md) | Memo, letter, news article or release, app or web page |
| [style-and-language.md](style-and-language.md) | Voice, tone, sentence patterns, wording to use and to avoid |

When the draft is done, use [../review-checklist.md](../review-checklist.md).

## What kind of document an HiMCM paper is

An HiMCM paper is a **technical report written for expert readers in a hurry**, usually with one **non-technical piece** (memo, letter, article, app design) for a named audience. In the corpus, the strongest papers share these features:

- **Answer-first.** The summary sheet and the start of each section say what was found, not only what was done.
- **Requirement-mapped.** Every requirement has a visible, labeled answer. Headings tagged with requirement numbers, a requirement-to-section table, or a restatement that the paper then follows in order.
- **Reasoned.** Every assumption has a justification, every method choice a reason, every constant an explanation.
- **Concrete.** One worked example traced through the model; real numbers with units; named data sources.
- **Honest.** Sensitivity analysis, limitations and strengths/weaknesses that are specific to the model.
- **Designed.** Flowcharts, clear tables and well-labeled figures carry much of the explanation, and the non-technical piece looks like the real thing (a memo with a header, an article with a headline).

## Rules come from the current statement

Page limits, required parts and their order, and format details are set each year by COMAP. From 2020 the statements set a 25-page limit that counts everything (summary sheet, table of contents, references, appendices); earlier papers in the corpus (2014–2019) are often 30–60 pages or more because earlier rules differed. Always follow the current statement and contest instructions, including how to identify the paper (normally by team control number only).

## A writing schedule that works

The non-modeling work takes longer than teams expect. Plan for it:

1. **At the start**: set up the paper skeleton with headings that mirror the requirements. Decide who writes what.
2. **While modeling**: write assumptions, notation and data sections as decisions are made. Save every figure with a clear caption the moment it is final. Keep one table of headline numbers that all sections and the summary will quote.
3. **When results are stable**: write results, sensitivity, strengths and weaknesses, then the non-technical piece.
4. **Last**: write the summary sheet (from the finished paper, not the plan), the conclusion and the table of contents. Then do the review pass and check the page count.

Freeze the model before the final writing pass. Changing a weight after the figures are made is how text, tables and code drift apart (see the 2018A-8744 and 2020B-10839 cards).

## Ways to use the corpus for writing

- To see how a section was done well, open the "Writing and presentation worth learning" section of a paper card. It lists the summary structure, paper structure, devices, the non-technical piece and sample phrasing, all with page numbers.
- To see the real layout of a page (a memo, a figure-heavy results page, a summary sheet), open the PDF or render the page: `python3 tools/render_page.py <ID> <page>`.
- Study structure and technique, then write in your own words. Copying text from past papers is plagiarism.
