# Simulation and stochastic models

Use these when **randomness, space or individual behavior** matters and a closed-form answer is hard: plant spread (2023A), drone light shows (2017A), train and traffic flow (2014A, 2015A), epidemic spread (2014B), random search over schedules (2020B), generating test personas (2020A), or thermostat control (2018B).

## Methods used in the corpus

| Method | What it does | Corpus examples | Watch for |
|---|---|---|---|
| Monte Carlo over individuals | Simulate each seed or plant with random draws | [2023A-13643](../../papers/2023A-13643.md), [2023A-14076](../../papers/2023A-14076.md) (200,000 repetitions) | Enough runs; report mean and spread |
| Agent-based model | Agents follow rules (move, grow, die) on a daily step | [2023A-14632](../../papers/2023A-14632.md) | State every rule and its source |
| Cellular automaton | Grid cells change state by local rules | [2023A-13719](../../papers/2023A-13719.md) (1 m² cells, daily step) | Cell size and boundary handling |
| Stage (Leslie) matrix | Counts by life stage, projected by matrix powers | 2023A-14076 | Pair with a spatial model if "where" matters |
| Dispersal kernels and random walks | Distance and direction distributions; Lévy flight; Brownian motion | 2023A-14076 (gamma calibrated to a published percentile), [2023A-14140](../../papers/2023A-14140.md) (Lévy flight), 2023A-14632 (Brownian with Poisson moves) | Calibrate to data; check the fit (2023A-14076 used a chi-square test) |
| Monte Carlo search | Sample random candidate solutions, keep the best | [2020B-10876](../../papers/2020B-10876.md), [2020B-10839](../../papers/2020B-10839.md) | Show convergence (2020B-10876, p. 12) |
| Monte Carlo Tree Search | Search a decision tree by random playouts | [2018B-8506](../../papers/2018B-8506.md) | Explain the state, actions and reward |
| Monte Carlo generation of test cases | Draw personas or scenarios from defined option sets | [2020A-10550](../../papers/2020A-10550.md) (p. 15) | Fix inconsistent draws, as 2020A-10550 did |
| Monte Carlo sensitivity | Sample parameters within ±10% and summarize output change | 2023A-14632 (RMSE radar chart) | Report which parameters matter most |
| Empirical probability distributions | Probability of an event from observed frequencies | 2018B-8506 (return-time pmf) | Sample size |
| Expected values for probabilistic factors | Replace a random quantity with its expectation | [2020A-10701](../../papers/2020A-10701.md) (overtime) | Fine for averages; not for risk |
| Queueing and cellular-flow simulation | Represent arrivals, service capacity and local movement explicitly | [2014A-4671](../../papers/2014A-4671.md), [2015A-6080](../../papers/2015A-6080.md) | Calibrate arrival, speed and reaction assumptions; report the bottleneck metric |
| Epidemic compartment simulation | Track susceptible, exposed, infected, recovered or dead states under uncertain parameters | [2014B-4637](../../papers/2014B-4637.md), [2014B-4880](../../papers/2014B-4880.md) | Separate biological uncertainty from Monte Carlo error and show intervention scenarios |

## Good practice seen in the corpus

- **Model the whole process when timing matters.** In 2023A only a few generations fit in a year, so life-cycle timing mattered as much as dispersal (2023A problem card). 2023A-13719 modeled germination, growth and dispersal together.
- **Calibrate to one published number when that is all you have.** One percentile can pin down a one-parameter distribution (2023A-14076, p. 9).
- **Separate "how many" from "where"** (2023A-14076, p. 8).
- **Treat unspecified conditions as variables**: start month (2023A-13643), plot orientation under real winds (2023A-13719).
- **Present stochastic output clearly**: a representative run, maps at several times, mean and spread over many runs, stage-colored scatter plots (2023A problem card).
- **Give pseudocode** for the simulation loop (2023A-13643, pp. 9–10, 20).
- **Use enough repetitions.** Five runs per scenario is thin for statistical comparison (see the note in 2023A-13719).

## Outside the corpus

Not seen in the carded papers, but often suitable:

- **Discrete-event simulation** for queues, evacuations, service systems and traffic: events happen at random times and the simulation jumps from event to event.
- **Queueing models** (M/M/c and similar) for waiting times and staffing, either as a closed-form check or as the model itself.
- **Markov chains** for systems that move between a few states with fixed probabilities (health states, customer status, weather regimes).
- **Epidemic-type compartment models** (SIR and variants) for anything that spreads by contact, including information and adoption.
- **Variance reduction and confidence intervals** for Monte Carlo estimates: report the standard error and the number of runs needed for the precision you claim.
- **Seeded random number generators**, so results can be reproduced and the code checked.
