"""Reproduce synthetic model-selection examples; no observed city data.
Run: python3 projects/himcm2026A/analysis/model_examples.py
Dependencies: numpy, scipy.
"""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import linprog

def simplex_max_margin(values, city):
    others = [k for k in range(len(values)) if k != city]
    inequalities = np.array([
        np.r_[-(values[city] - values[k]), 1.0] for k in others
    ])
    answer = linprog(
        [0.0] * values.shape[1] + [-1.0],
        A_ub=inequalities, b_ub=np.zeros(len(others)),
        A_eq=[np.r_[np.ones(values.shape[1]), 0.0]], b_eq=[1.0],
        bounds=[(0.0, 1.0)] * values.shape[1] + [(None, None)],
        method="highs",
    )
    if not answer.success:
        raise RuntimeError(answer.message)
    return {"margin": float(answer.x[-1]), "weights": answer.x[:-1].tolist()}

def scenario_regrets(values):
    return (values.max(axis=0) - values).max(axis=1)

def credibility(a, b, weights, q, p, veto):
    difference = b - a
    concordance = np.clip((p - difference) / (p - q), 0.0, 1.0)
    discordance = np.clip((difference - p) / (veto - p), 0.0, 1.0)
    aggregate = float(weights @ concordance)
    opponents = discordance[discordance > aggregate]
    if len(opponents):
        return float(aggregate * np.prod((1.0 - opponents) / (1.0 - aggregate)))
    return aggregate

values = np.array([[1.0, 0.2], [0.2, 1.0], [0.55, 0.55]])
margins = [simplex_max_margin(values, i) for i in range(3)]
geometric = np.sqrt(np.prod(values, axis=1))
assert margins[2]["margin"] < 0.0
assert geometric.argmax() == 2

lp_regrets = []
for i in range(3):
    gains = []
    for k in range(3):
        answer = linprog(
            -(values[k] - values[i]), A_eq=[[1.0, 1.0]], b_eq=[1.0],
            bounds=[(0.0, 1.0)] * 2, method="highs",
        )
        if not answer.success:
            raise RuntimeError(answer.message)
        gains.append(-answer.fun)
    lp_regrets.append(max(gains))
ideal_gap = (values.max(axis=0) - values).max(axis=1)
assert np.allclose(lp_regrets, ideal_gap)

two_scenarios = np.array([[0.95, 0.20], [0.85, 0.35]])
original = scenario_regrets(two_scenarios)
squared = scenario_regrets(two_scenarios ** 2)
assert original.argmin() == 1 and squared.argmin() == 0

a = np.array([0.95, 0.20, 0.95])
b = np.array([0.70, 0.80, 0.70])
weights = np.array([0.4, 0.2, 0.4])
q = np.array([0.02, 0.02, 0.02])
p = np.array([0.10, 0.10, 0.10])
veto = np.array([np.inf, 0.30, np.inf])
ab = credibility(a, b, weights, q, p, veto)
ba = credibility(b, a, weights, q, p, veto)
assert np.isclose(ab, 0.0) and np.isclose(ba, 0.2)

# Joint qualification: marginal compliance does not imply joint compliance.
both_fail_independently = (1.0 - 0.05) ** 7

result = {
    "data_type": "synthetic examples only",
    "pareto_vs_possible_winner": {
        "cities": ["A", "B", "C"], "values": values.tolist(),
        "max_margin_lp": margins, "equal_weight_geometric": geometric.tolist(),
        "interpretation": "C is nondominated and can beat each rival separately, but cannot win an additive ranking under any single common weight vector; it wins the geometric ranking at equal weights."
    },
    "simplex_regret_identity": {
        "lp_regrets": lp_regrets, "maximum_gap_to_ideal": ideal_gap.tolist()
    },
    "regret_scale": {
        "values": two_scenarios.tolist(),
        "regrets_original": original.tolist(), "regrets_squared": squared.tolist(),
        "winner_original": "B", "winner_squared": "A"
    },
    "geometric_zero": {
        "X": [0, 1, 1, 1, 1, 1, 1], "Y": [0.01] * 7,
        "X_score": 0.0, "Y_score": 0.01
    },
    "relative_veto": {
        "credibility_A_over_B": ab, "credibility_B_over_A": ba,
        "cut": 0.65, "relation": "incomparable at the illustrative cut"
    },
    "joint_qualification": {
        "individual_probability": 0.95, "independent_constraints": 7,
        "joint_probability": both_fail_independently
    },
}
path = Path(__file__).with_name("model_examples.json")
path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
