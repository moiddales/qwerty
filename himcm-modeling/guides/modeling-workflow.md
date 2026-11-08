# Modeling and data analysis workflow

This guide covers the work between choosing a direction and writing: assumptions, data, building the model, solving it, and checking it. For choosing a method, see the [model catalog](model-catalog/README.md). Examples cite paper cards; page numbers refer to each paper's PDF.

## 1. Assumptions: few, necessary and justified

- **Write each assumption with its justification.** Assumption–justification pairs are the most common format in the corpus (2018A-8554, 2018B-8506, 2020B-10839, 2021A-11462 and many others). A justification can be a cited fact, a data observation, a scale argument ("negligible compared with ...") or a scoping decision.
- **Make every assumption do work.** Each one should simplify the model, fill a data gap or set the scope. Assumptions like "the data are accurate" add little; an assumption that changes a result should be tested later.
- **Use data for the justification when possible.** 2021A-11900 justified a family of three with the EIA average of 2.48 people per household, and 900 kWh per month with the EIA annual figure and the state-level range (pp. 5–6).
- **Turn assumptions into conveniences openly.** "In this way, all directions have same odds and we can pin the dandelion on an arbitrary edge." (2023A-13643, p. 5)

## 2. Variables and notation

- A notation table (symbol, meaning, unit) near the start is standard. Several papers also gave a local table before each sub-model (2018A-8700, pp. 28–30; 2021A-11931 Tables 1 and 4).
- Define each term the first time it is used. 2023A-14632 introduced "hyperparameters" with a one-sentence definition before using the word (p. 9).
- Keep units on every quantity. Unit slips are among the most common errors in the corpus (see section 7).

## 3. Data: collect, clean, document

**Given data**

- Report what is missing and how much. 2018A papers reported missing shares variable by variable (for example, G-force about 73% missing in 2018A-8744, p. 8).
- **Impute with a method you can check**, and show the check: R² or test error, before/after distributions or correlations (2018A-8992 compared correlation heatmaps before and after imputation, pp. 10–11; 2018A-8700 reported a 3% imputation error, p. 1). Use physics when it applies: 2018A-8874 recovered missing speeds and G-forces from mechanical relations.
- **Check outliers against sources before deleting them.** A record value can be the most important data point in a "best of" ranking (2018A-8700 deleted a real 14-inversion record as a z-score outlier; see its card).
- Say what you dropped and why (2018A-8700 gave a reason table for rejected indicators, pp. 12–13).

**Collected data**

- Name every source and keep a provenance table (2023A-13719 had a data-provenance table; 2024B-16226 a data-source table, p. 5).
- Prefer authoritative public sources: government statistics, international agencies, peer-reviewed studies, manufacturer specifications. 2020A-10656 built a traceable pipeline from the BLS handbook, child-labor rules, OSHA risk tiers and O*NET wages (pp. 6–7).
- **Label generated, assumed or illustrative data as such.** If the code creates data, say so in the text (see the note in 2024B-16226).
- When filling gaps with defaults, use realistic values and test them (see the efficiency note in 2021A-11931).

## 4. Build the model step by step

- **Start with a baseline, then add.** 2023A-14140 started from a negative-exponential kernel, then added Lévy flight, mortality and climate, noting the limitation of each step (p. 5 onward). 2018A-8744 added one factor at a time with a numbered equation for each (Eqs. 5.1–5.7).
- **Show a failed attempt when it explains the choice.** 2023A-14076 fitted a normal distribution, got a mean of about −314 m, and rejected it: "which is not sensible, since the average dispersal distance cannot be far below zero." (p. 9). 2021A-11900 tried the entropy weight method and explained why it was set aside (p. 19).
- **Derive functional forms from required behavior** (limits, monotonicity, saturation), or fit them to data, and say which you did. 2023A-13719 was candid that its germination curve borrowed the shape of a normal CDF only for its trend and asymptote (p. 9).
- **Explain every constant.** The strongest hand-built models give each constant a purpose and a worst-case effect: "the constant 0.7 was picked since (0.7)² = 0.49, meaning this term will, at worst, roughly halve the score." (2020A-10656, p. 9). 2021A-11931 calibrated each penalty rate so that a stated tolerance gives a penalty of 1 (pp. 11–12).
- **Make the decision variable explicit** in optimization and scheduling (start years in 2020B; pack size n in 2021A-11931 and 2021A-11462). Write the objective's direction clearly (minimize or maximize).
- **Separate hard constraints from trade-offs.** Filters or zero factors for what cannot be compensated, weights for the rest (2020A problem card).

## 5. Solve, and keep a worked example

- **Trace one case through every step** before reporting batch results: Christopher in 2020A-10549 (pp. 10–16), the Tesla Powerwall 2 in 2021A-11931 (pp. 17–19), a four-project toy schedule in 2020B-10876 (pp. 11–12), one persona in 2018A-8744. A worked example lets a judge verify the method and is one of the most reusable devices in the corpus.
- **For stochastic methods**, show convergence (2020B-10876 plotted the best value against the number of samples, p. 12), use enough runs, and report the mean and spread rather than one run.
- **Keep the text, the formulas and the code in agreement.** Several Outstanding papers lost traceability because printed weights or signs differed from the code (2018A-8744 card). Freeze the model before writing the results.

## 6. Validate: show the model is believable

No single test is required. Choose the checks that suit the model and the data, and report them honestly. Checks used in the corpus:

| Check | When it fits | Corpus examples |
|---|---|---|
| Hold-out or back-test | Forecasts and fitted models with enough data | Cross-validation with only 63 points (2022B-12465, pp. 4–5, 18); back-tests in 2021B-11898 and 2021B-11823 |
| Comparison with an independent figure | Estimates of quantities that someone has published | HPC energy against the IEA range (2024B-15022, p. 7); budget against a commercial kit price (2021A-11462) |
| Comparison with other rankings, as a diagnostic | Rankings | Disagreements with online lists explained, and a modeling artifact found and fixed (2018A-8874, 2018A-8700) |
| Physical or logical limits | Long extrapolations | 2050 lake level compared with dead pool (2021B-11898, p. 14) |
| Face validity on cases with known answers | Classifiers and indices | Index tested on non-invasive plants as a negative control (2023A-14076, p. 23) |
| Persona plausibility | Personalized recommenders | Results read against each persona's story (2020A, all five papers) |
| Discrimination | Personalized recommenders | Two near-identical personas should get different results (2020A-10550, p. 19) |
| Baseline comparison | When added complexity needs justifying | Lexicographic baseline vs the full model (2020A-11135, pp. 18–19) |
| Internal consistency | AHP and similar | Consistency ratio, and repair of inconsistent judgments (2020A-10549, pp. 18–20) |
| Convergence | Random search, Monte Carlo | 2020B-10876, p. 12 |

Avoid circular validation: thresholds set after looking at the results cannot then confirm them (see the 2023A-14140 card), and agreement with self-generated data shows internal consistency, not real-world accuracy (2018B-8506 card).

## 7. Sensitivity and uncertainty

Sensitivity analysis appears in most strong papers. The best ones connect it to a decision.

- **One-at-a-time perturbation** of inputs and weights (±10% of every input and weight in 2021A-11931, pp. 19–20).
- **Find the flip point.** At what weight does the top choice change? 2020A-11135 called this the "Absolute-Top factor" (pp. 21–22). 2020A-10550 also varied the modeller's own structural weights, not only the user's (pp. 18–19).
- **Sweep a parameter and turn the curve into a recommendation.** 2020B-10876 swept the annual budget and recommended the knee of the curve, 1.3 times current giving (pp. 16–17).
- **Grid over two parameters** and show a heatmap or table of the outcome (2024B-15502's renewable × nuclear heatmap, p. 18; PUE × demand tables, p. 7).
- **Report bounds as intervals tied to named parameter ranges**, especially when a requirement asks for "realistic bounds" (2024B problem card).
- **Test the assumptions that drive the answer**: the decay rate in 2020B-10876 (Fig. 14), the yearly budget in 2023B-13694 (p. 22), the plot orientation under real winds in 2023A-13719 (pp. 13–15).

## 8. Common technical slips (worth a final check)

These come from the "Notes for reuse" sections. They appear in Outstanding papers, which shows judges forgive some of them, but each one weakens a paper.

- **Units and arithmetic**: cubic meters treated as liters (2021A-11900 card); a share computed wrongly (2024B-15022 card). Recompute headline numbers by hand.
- **Long extrapolation from a short window**: months of data carried to 2050 (2021B problem card), ARIMA or grey models on four points (2024B-15502 card). Report the window, compare with limits, call such results scenarios.
- **A growth rate applied to a different quantity than the one it was measured on** (2024B-15022 card).
- **An index whose direction does not match its meaning**: a "harm" score that rises when native species grow (2023A-14632 card).
- **Weights that collapse onto one variable**: entropy weighting can put almost all weight on a variable just because it varies most, including imputed variables (2018A-8554 card).
- **Unsourced constants that drive the result.** Either cite them or vary them.
- **Different values for the same quantity in different sections** (the summary vs the body vs the memo). Keep one source of truth for every reported number.
- **Results not reported in the form asked.** If the statement asks for values in 2025, 2030 and 2050, give the numbers, not just a plot (2021B-11823 card).

## 9. Strengths and weaknesses

Nearly every paper ends its modeling with strengths and weaknesses. Make them specific to your model and honest; generic lines ("our model is simple") add nothing. Good examples organize them by stage (interpretation, data, model, testing in 2020A-10656, p. 16) or place them right after each model (2023A-14140). A weakness you name and partly address in a sensitivity test reads better than one a judge discovers.
