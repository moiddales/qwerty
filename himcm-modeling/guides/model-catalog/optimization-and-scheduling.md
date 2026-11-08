# Optimization and scheduling

Use these when the task is to **choose the best plan under constraints**: fund projects over years with a budget (2020B), replace a bus fleet (2023B), pick a battery system size (2021A), choose a mix of treatment facilities (2021B), plan drone paths without collisions (2017A).

## The basic recipe

1. **Decision variables**: what you choose (start years, numbers of units, which facilities, a replacement schedule).
2. **Objective**: what "best" means, with its direction (minimize cost, maximize benefit or cost-effectiveness). If there are several objectives, say how they are combined or traded off.
3. **Constraints**: budget per year, capacity, continuity, physical limits.
4. **Solution method**: exact (enumeration, integer programming) when the problem is small enough; heuristic or random search when it is not, with a convergence check.
5. **Sensitivity**: how the plan changes when the budget or key parameters change, and what that means for the decision-maker.

## Methods used in the corpus

| Method | Corpus examples | Watch for |
|---|---|---|
| Integer programming (branch and bound) | [2021B-11576](../../papers/2021B-11576.md) (facility mix) | Write the model fully; check the solution satisfies every constraint |
| Constrained nonlinear optimization (COBYLA) | [2021B-11823](../../papers/2021B-11823.md) (different objectives for water-scarce and cash-poor cities) | Say why the objective differs by case |
| Exhaustive enumeration / depth-first search | [2023B-13694](../../papers/2023B-13694.md) (10-year replacement schedules under a budget) | Show the search space is small enough |
| Enumeration of the number of units | [2021A-11931](../../papers/2021A-11931.md), [2021A-11462](../../papers/2021A-11462.md) | Let the count be a variable so options of different sizes compete fairly |
| Priority order + greedy decoding + random search | [2020B-10876](../../papers/2020B-10876.md) (pp. 10–12) | Decoding guarantees feasibility; plot convergence |
| Random search with filtering and ranking | [2020B-10839](../../papers/2020B-10839.md) | Justify how objectives are combined into one score |
| Monte Carlo Tree Search | [2018B-8506](../../papers/2018B-8506.md) (daily temperature plan) | Explain the search space; 2018B-8506 argued its size was manageable (p. 16) |
| Greedy matching and geometric construction | [2017A-7359](../../papers/2017A-7359.md) (farthest-first point matching, staggered departures) | Present heuristic guarantees as heuristics, backed by simulation |

## Good practice seen in the corpus

- **Find what makes timing matter.** 2020B-10876 linked delay to falling feasibility, which gave the schedule its real trade-off (pp. 8–10).
- **Design for a stated worst case** when sizing (the longest night plus a cloudy day in 2021A-11462).
- **Show a toy example** of the algorithm before the full problem (2020B-10876's four-project demo, pp. 11–12).
- **Give the decision-maker scenarios**: constant, growing and optimized budgets, and a quantified answer to how much more money to raise (2020B-10876, pp. 13–17).
- **Handle outliers openly.** 2020B-10876 explained why one project could not fit a flat budget and when it could (pp. 13–14).
- **Respect the decision-maker's practical limits.** 2021B-11576 spread facility construction over years because building everything at once "will create a huge budget gap" (p. 20).
- **Check what the objective rewards.** A sum of benefit/cost ratios favors cheap projects; compare with total benefit under the budget (see the note in 2020B-10876).

## Outside the corpus

Not seen in the carded papers, but often suitable:

- **Linear programming** with a standard solver (for example `scipy.optimize.linprog`, PuLP, or a spreadsheet solver) for allocation problems; the dual values (shadow prices) tell you what an extra unit of budget is worth.
- **Knapsack formulations** for "which projects to fund this year".
- **Dynamic programming** for multi-stage decisions where today's choice changes tomorrow's options.
- **Multi-objective optimization**: plot the Pareto front of cost against benefit and let the client choose, instead of fixing weights in advance.
- **Goal programming** when there are targets to reach rather than quantities to maximize.
- **Genetic algorithms and simulated annealing** for large combinatorial problems, with convergence plots and several runs from different starts.
- **Network flow and shortest-path models** (Dijkstra, minimum-cost flow) for routing, evacuation and logistics.
- **Robust optimization or scenario-based optimization** when parameters are uncertain: choose the plan that performs acceptably across scenarios.
