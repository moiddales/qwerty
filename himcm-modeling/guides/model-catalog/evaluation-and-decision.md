# Evaluation and multi-criteria decision models

Use these when the task is to **rank, choose or score** options against several criteria: summer jobs (2020A), batteries (2021A), roller coasters (2018A), the impact of invasive plants (2023A), project priorities, Olympic events (2024A), or ski-resort alternatives (2017B).

## The basic pipeline

1. **Criteria.** List them, justify each, and drop or merge strongly correlated ones so a feature is not counted twice (2018A-8744 kept height and dropped drop, r = 0.95, pp. 10–11; 2018A-8992 grouped correlated variables, which also cut the number of user questions from 28 to 3, p. 22).
2. **Scoring each criterion.** Normalize to a common scale with the right direction: benefit (more is better), cost (less is better) or **ideal point** (a moderate value is best). Use transformations when distributions are very skewed (Box-Cox in 2018A-8744 and 2020A-11135).
3. **Weights.** Subjective (AHP, ANP, survey, user input), objective (entropy weight method) or a blend.
4. **Aggregation.** Weighted sum, TOPSIS distance to ideal, product of factors, or a penalty sum.
5. **Checks.** Consistency, sensitivity of the ranking to the weights, comparison with a baseline or external ranking.

## Methods used in the corpus

| Method | What it does | Corpus examples | Watch for |
|---|---|---|---|
| Weighted sum of normalized scores | Simple, transparent aggregate | Most ranking papers | Normalization choice and direction of each criterion |
| AHP | Weights from pairwise comparisons; consistency ratio checks coherence | [2020A-10549](../../papers/2020A-10549.md), [2020A-10701](../../papers/2020A-10701.md), [2020A-11135](../../papers/2020A-11135.md), [2021A-11900](../../papers/2021A-11900.md), [2023A-13643](../../papers/2023A-13643.md) | Whose judgment the matrix encodes; report CR; test weight sensitivity |
| AHP inconsistency handling | Point to or repair the most inconsistent comparison | 2020A-11135 (p. 8), 2020A-10549 (pp. 18–20) | Explain the repair rule |
| ANP | Like AHP but criteria can influence each other (supermatrix) | [2020A-10550](../../papers/2020A-10550.md), [2023A-13719](../../papers/2023A-13719.md) | Justify the interdependence; more judgments to document |
| Entropy weight method | Objective weights from how much each criterion varies across options | [2018A-8554](../../papers/2018A-8554.md), [2018A-8700](../../papers/2018A-8700.md), 2020A-10549, [2023A-14140](../../papers/2023A-14140.md) | Rewards dispersion, not importance; can load almost all weight on one (even imputed) variable; depends on the option set |
| Subjective + objective blend | Combine AHP or fuzzy weights with entropy weights | 2020A-10549, [2018A-8874](../../papers/2018A-8874.md), 2023A-14140 | State and test the blending ratio |
| TOPSIS | Rank by distance to an ideal and an anti-ideal option | 2020A-10701, 2023A-13719 | Sensitive to normalization and to which options are included |
| Fuzzy methods | Model vague judgments with fuzzy numbers | 2018A-8874 (LFPP), 2018A-8700 (fuzzy comprehensive evaluation) | Document how answers become fuzzy numbers |
| Grey relational analysis | Screen or rank indicators by similarity to a reference | 2018A-8700 | Justify the reference series |
| Hand-built score with gates and penalties | 0/1 factors for unacceptable options; decaying penalties for shortfalls | [2020A-10656](../../papers/2020A-10656.md) (pp. 7–10) | Argue every constant (2020A-10656 does) |
| Requirement-gap ("disparity") scoring | Score each option by how far it falls short of the user's needs | [2021A-11931](../../papers/2021A-11931.md) | Calibrate penalty constants to stated tolerances |
| Gaussian ideal-point index | Preferred range becomes a bell curve | 2020A-11135 (pp. 11–12) | Width of the curve is a modeling choice |
| Benefit/cost ratio | Score divided by a cost (hours, money) | 2020A-11135; 2020B-10876 (benefit × feasibility / cost) | Ratios favor cheap options; also compare total benefit under a budget |
| Rubric scoring | Point levels with descriptors for each criterion | [2023A-14076](../../papers/2023A-14076.md) | Justify maxima; show each option's score as an explicit sum |
| Clustering of results | Return a shortlist or a diverse set instead of one winner | 2020A-10549 (k-means), 2020A-10701 (hierarchical) | Explain why a set is more useful than a single answer |
| Two-dimensional score | Keep harm and benefit as a pair rather than one number | [2023A-14632](../../papers/2023A-14632.md) | The dividing line needs a reason and a sensitivity test |
| Combined weighting with Monte Carlo TOPSIS | Blend expert and data-derived weights, then repeat the ranking under perturbed weights | [2024A-14995](../../papers/2024A-14995.md) | Report ranking stability and show which indicators drive reversals |
| Spatial multi-criteria design | Combine terrain, access, safety and service criteria while retaining a map or network | [2017B-8121](../../papers/2017B-8121.md), [2017B-8124](../../papers/2017B-8124.md) | Do not hide spatial feasibility inside one score; map the selected design |

## Good practice seen in the corpus

- **Separate hard constraints from trade-offs.** Filter out infeasible options first (decision tree in 2020A-11135; age gate in 2020A-10549; zero factors in 2020A-10656).
- **Let the user's situation change the scores, not only the weights.** Net pay after commuting (2020A-10701, 2020A-11135), the number of batteries needed (2021A-11931, 2021A-11462).
- **Match the user interface to the model's inputs** so the presentation is buildable (2020A-10656 website buttons use the model's scales, p. 15).
- **Find the flip point.** Report the weight at which the top choice changes (2020A-11135, pp. 21–22).
- **Explain results from the scores.** Say why an option ranks high or low using its criterion values (2020A-10701, p. 16; 2023A-13643, p. 21).
- **Use an alternative method as a check and say what you conclude** (2021A-11900 rejected entropy weights with a reason, p. 19).
- **Publish the raw scoring matrix** when scores are judgments, so results can be traced (see the note in 2023A-14140).

## Outside the corpus

Not seen in the carded papers, but often suitable:

- **Pareto (non-dominated) screening** before any weighting: remove options that are worse on every criterion than some other option. This is cheap and needs no weights.
- **Weight-space sensitivity by Monte Carlo**: sample many weight vectors (for example from a Dirichlet distribution) and report how often each option ranks first. This gives a robustness statement for the ranking without trusting one weight set.
- **Utility functions with diminishing returns** (for example logarithmic utility of income) when "more is better, but less so at high values".
- **Outranking methods** (PROMETHEE, ELECTRE) when criteria are not freely compensable.
- **Data envelopment analysis** to measure the efficiency of options that turn several inputs into several outputs.
- **Rank-correlation measures** (Spearman, Kendall tau) to compare your ranking with another quantitatively. 2018A-8874 defined Kendall tau distance; using it to quantify agreement is a natural step.
