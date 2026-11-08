# Structure and sections

## Overall organization

Almost every paper in the corpus follows a recognizable spine:

> Summary sheet → (non-technical piece, if placed up front) → Table of contents → Introduction (background, restatement, our work) → Assumptions with justifications → Notation → Data → Model(s) → Results → Sensitivity / validation → Strengths and weaknesses → Conclusion → (non-technical piece, if placed at the end) → References → Appendix (code)

Within that spine, two organizations both worked:

- **By method stage**: assumptions, data, model, results and sensitivity for the whole paper. This suits problems where one model answers all the requirements (2020B-10876, 2021A-11931).
- **By requirement**: one major section per requirement, each with its own model, results and sometimes its own assumptions (2023B-13694 tagged sections "Req. 1–4"; 2024B-15022 and 2024B-16226 used requirement or task numbers as headings; 2021B-12384 made each part a self-contained module, pp. 4, 9, 17). This suits problems whose parts need different models.

A useful hybrid repeats one sub-structure inside each model section. 2018A-8992 used approach, variables, assumptions, results, sensitivity, strengths/weaknesses for each model; 2023B-13694 used variables table, evaluation factors, construction, application, sensitivity.

**Make the map visible.** Tag headings with the requirements they answer ("(For question 1a/1b)", 2020B-10876, p. 5; "(Questions 1 and 2)", 2020A-10549, p. 7), or give a requirement-to-section table (2024B-15502, p. 3).

## Section by section

### Table of contents

Short and accurate, usually on page 2. Some papers add a list of tables (2021A-11931, p. 3). It costs a page of the limit, so keep it compact (2023A-14632 used two columns).

### Introduction

- **Background**: a short paragraph on why the problem matters, with one or two sourced facts. Avoid long history.
- **Restatement**: the requirements in your own words, often as a numbered list. Strong restatements also say how you interpret ambiguous terms (2020A-10550 defined "best job" in one sentence, p. 3) and correct errors in the statement if any (2022B-12465, pp. 3–4).
- **Our work / problem analysis**: a roadmap of the approach, often as a flowchart (2020B-10876, 2020A-10701 p. 5, 2021B-11823 p. 6). A short "Problem analysis" section planning the answer to each requirement before any model is a strong device (2017A-7359 pp. 5–7; 2020A-10550 p. 4; 2022B-12465 pp. 4–5).
- **Literature review** (optional): a few sentences positioning your approach among existing ones (2018A-8700 sorted existing rankings into quantitative and subjective, p. 6).

### Assumptions

Numbered assumption–justification pairs, either as one section or placed in each model section where they are used (2018A-8992 and 2023A-13643 put assumptions inside each model). Keep only assumptions that matter. See [../modeling-workflow.md](../modeling-workflow.md).

### Notation

A table of symbols, meanings and units. Local tables before each model help when there are many symbols.

### Data

Sources, cleaning, missing values and imputation, with the checks (before/after plots, R²). A provenance table makes sources easy to verify. If you generated or assumed any data, say so here.

### Model sections

For each model:

1. **Why this model**: one or two sentences linking it to the question.
2. **Build-up**: equations introduced one at a time, each followed by a plain-language reading of what it means and why it has this form. 2020A-10656 explained every formula term in plain words with its range and edge cases.
3. **Parameters**: values and sources, or how they were calibrated.
4. **Worked example**: one case traced through every step (see [figures-tables-equations.md](figures-tables-equations.md)).
5. **Algorithm**: numbered steps, pseudocode or a flowchart for anything computational.

Define a term before you use it: "We use the term hyperparameters to designate global values that are not directly passed into our model but still change the output of the model." (2023A-14632, p. 9)

### Results

- **Answer the requirement directly and first**, then show the supporting tables and figures.
- **Give the numbers asked for** in a table, not only in a plot. The 2021B-11823 card notes forecast values that could only be read off dense plots.
- **Interpret the results.** Say why the top option is on top, using the model's own terms: "Since the student's weighting for salary is also high, it's reasonable that the medium knowledge index can't compensate for the low salary and time index." (2020A-10701, p. 16)
- **Signpost disagreements**: "Then comes the question: How can we explain the difference between the votes and our list?" (2018A-8554, p. 13)
- **Point out surprises and explain them**: "Thus, paradoxically, a more 'suitable' climate could result in lower seed survival due to density-induced mortality." (2023A-14140, p. 15)

### Sensitivity analysis and validation

A section of its own, or a subsection of each model. Say what was varied, by how much, what changed, and what that means for the conclusion. See [../modeling-workflow.md](../modeling-workflow.md), sections 6–7.

### Strengths and weaknesses

Specific to your model, honest, and usually 3–5 of each. A weakness can come with a mitigation or a further-work note. Organizing them by stage (2020A-10656, p. 16) or placing them after each model (2023A-14140, 2021A-11900) both worked.

### Conclusion

Restate the answer to each requirement with its key number, the recommendation, and the main limitation. 2024B-15502 used a numbered conclusion that restated each result with its number (pp. 23–24). Do not introduce new results here.

### References

Cite every data source, formula source and fact. Use a consistent style. Inline bracketed citations next to data tables, as in 2021A-11462's appliance table (p. 6), make verification easy.

### Appendix

Code, full data tables, full rankings. It counts toward the page limit under current rules, so include what supports the paper and no more. Judges read the body; the appendix is for checking.

## Placement of the non-technical piece

Papers placed the memo, letter or article either right after the summary (2018A-8554, 2020A-10549, 2021A-11900, 2021B-11552, 2018B-8506) or at the end (2020B-10839, 2022B-12465, 2023B-13694, 2024B-15502, 2024B-16226). Both worked. Follow the statement if it specifies an order. Putting it up front means it is read early; putting it at the end lets it summarize results the reader has already seen.

## Page budget

With a 25-page total, a typical split is about: summary 1, contents 1, introduction and assumptions 3–4, models and results 12–14, sensitivity and strengths/weaknesses 2–3, non-technical piece 1–2, references 1, appendix 1–2. Adjust to the problem, but decide the budget early so the last requirement is not squeezed into half a page.
