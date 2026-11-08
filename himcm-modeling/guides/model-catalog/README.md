# Model catalog

This catalog helps you choose methods. It is **not a list of approved models**. Each family file says when the family fits, how Outstanding papers used it (with links to cards), what to watch for, and which useful methods outside the corpus are worth considering.

- Methods marked **Outside the corpus** were not seen in the carded papers. They are included because they suit typical HiMCM problems. Their absence from the corpus is not evidence against them.
- Counts in [catalog.md](../../catalog.md) describe this sample of papers only. A frequent method is not a better method.

## Choosing a method

Start from the question, not from the method:

1. **What output does the requirement ask for?** A ranking, a number with bounds, a forecast, a schedule, a yes/no classification, a map of spread, a recommendation.
2. **What does the data support?** How many points, how much missing, over what time span. Thirty annual values cannot support a complex time-series model to 2050; a plain trend with honest bounds may be better.
3. **Is there a mechanism you can write down?** A balance (water in minus water out), a physical law, a population process. Mechanistic models extrapolate better and are easier to defend than curve fits.
4. **Who will use the result?** A homeowner, a city council or a student needs a model whose logic can be explained in one paragraph and whose inputs they can change.
5. **How much time is left?** A simple model finished, checked and explained beats an advanced one half done.

Then justify the choice in the paper in one or two sentences: why this method fits this question better than the obvious alternatives. 2020A-10550 chose ANP over AHP because the criteria influence each other (p. 7); 2024B-15502 matched a grey model, a saturating ODE and ARIMA each to the behavior of a different driver.

## Problem features and candidate methods

| Feature of the problem | Candidate methods | Family file |
|---|---|---|
| Choose or rank options against several criteria | Weighted scores, AHP/ANP, entropy weights, TOPSIS, hand-built scores with gates and penalties; *outside the corpus:* Pareto screening, PROMETHEE, utility functions | [evaluation-and-decision.md](evaluation-and-decision.md) |
| Personal preferences must drive the result | User-set weights, ideal-point or range preferences, requirement-gap (shortfall) scoring | [evaluation-and-decision.md](evaluation-and-decision.md) |
| Relationship between variables; fill missing data | Correlation, regression, transformations, clustering, imputation | [statistics-and-forecasting.md](statistics-and-forecasting.md) |
| A trend over time; forecast | Trend tests, regression on time, exponential smoothing, ARIMA, grey models, decomposition | [statistics-and-forecasting.md](statistics-and-forecasting.md) |
| Spread, movement or random events in space and time | Monte Carlo, agent-based models, cellular automata, stage matrices, random walks | [simulation-and-stochastic.md](simulation-and-stochastic.md) |
| Allocate a budget or schedule projects | Integer programming, enumeration, greedy decoding with random or heuristic search | [optimization-and-scheduling.md](optimization-and-scheduling.md) |
| Size a system to meet a need | Worst-case requirement plus cost minimization over the number of units | [optimization-and-scheduling.md](optimization-and-scheduling.md) |
| A physical, economic or population mechanism | Balance equations, physical laws, geometry, differential equations, competition models, life-cycle accounting | [mechanistic-models.md](mechanistic-models.md) |
| Estimate a quantity nobody publishes | Top-down proxy and bottom-up build, cross-checked against each other or an external figure | [mechanistic-models.md](mechanistic-models.md) |

Most strong papers combine families: a mechanistic or statistical core, an evaluation or optimization layer for the decision, and simulation or sensitivity analysis for uncertainty.

## Rules of thumb from the corpus

- **One method, explained well**, usually beats several methods stacked without reasons. When a paper used two methods, the best ones compared them and drew a conclusion (2021A-11900 set aside entropy weights because the result contradicted domain knowledge, p. 19; 2020A-11135 compared its model with a simple baseline, pp. 18–19).
- **Every method needs a check suited to it**: a consistency ratio for AHP, a hold-out error for a forecast, convergence for a random search, a fit test for a distribution. See [modeling-workflow.md](../modeling-workflow.md), section 6.
- **Name software and give the code** (an appendix, or a note that code is available), but do not let code replace explanation.
