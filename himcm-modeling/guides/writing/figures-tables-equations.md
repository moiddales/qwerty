# Figures, tables, equations and worked examples

Strong HiMCM papers explain a large share of their work visually. A judge skimming the paper should be able to follow the approach from the flowchart, the key tables and the figure captions alone.

## Devices that recur in Outstanding papers

| Device | What it does | Corpus examples |
|---|---|---|
| Workflow / "Our work" flowchart | Shows the whole approach and how parts feed each other | 2020A-10701 (p. 5), 2021B-11823 (p. 6), 2021B-11576 (Fig. 1), 2024B-16226 (p. 4), 2023A-14140 |
| Requirement-to-section table | Maps each task to where it is answered | 2024B-15502 (p. 3) |
| Notation table | Symbols, meanings, units | Most papers |
| Assumption–justification table | Keeps assumptions and reasons together | 2024B-15502, 2023A-14632 |
| Data-provenance table | Source of every input | 2023A-13719, 2024B-16226 (p. 5) |
| Hierarchy or network diagram | Criteria structure for AHP/ANP | 2020A-10549 (p. 9), 2020A-10550 (p. 9, color-coded), 2018A-8874 (p. 16) |
| Worked toy example with figures | Shows an algorithm on a small case | 2020B-10876 four-project demo (pp. 11–12) |
| Convergence plot | Shows a stochastic search has settled | 2020B-10876 (p. 12) |
| Before/after plots | Show the effect of cleaning or transformation | 2018A-8744 Box-Cox, 2020A-11135 (p. 10), 2018A-8992 correlations |
| Heatmap or timetable | Shows a schedule or a grid of scenarios | 2020B-10876 timetable heatmaps; 2024B-15502 renewable × nuclear heatmap with values printed in cells (p. 18) |
| Small multiples | Same chart for several sites or cases | 2023A-13719 and 2023A-13643 map grids; 2024B-16226 pie panels (pp. 8, 10) |
| Radar chart | Compares profiles (user input vs chosen option) | 2020A-10656 (pp. 12–13), 2023A-14632 |
| Sensitivity curve with current value marked | Shows where a decision flips | 2020A-11135 (pp. 21–22) |
| Side-by-side comparison table | Your ranking vs others, before vs after a fix | 2018A-8554 (Table 6), 2018A-8874 (Tables 20, 23), 2020A-11135 (p. 18) |
| Sankey or flow diagram | Shows flows from sources to outcomes | 2024B-15502 (p. 10) |
| Pipeline diagram with step bands | Shows a model's stages | 2024B-15502 (pp. 4, 9) |
| Table of competing models' outputs | Shows how far candidate models disagree before one is chosen | 2022B-12646 (fit, test error and forecasts for five models, pp. 1, 12–14) |
| Maps of a spatial design | Show where the proposal sits on real terrain or geography | 2017B ski-resort papers; 2016B warehouse maps |
| Schedule or timetable for the reader | Gives the client something to act on | 2016A-6453 race-day start schedule (p. 3); 2020B-10997 funding schedule |
| Changed rows highlighted | Shows what an upgrade changed | 2024B-15502 model-upgrade table with changed rows in red (p. 22) |

## Figures

- **Every figure earns its place**: it shows something the text needs. Delete decorative charts.
- **Captions that stand alone.** Say what is shown and what to notice. 2022B-12465 wrote captions long enough that the figures can be read on their own; 2021B-12384 put the prediction value in the caption.
- **Label axes with units**, use readable font sizes, and keep colors consistent across figures (the same color for the same scenario everywhere).
- **Refer to every figure in the text** and say what it shows before or right after it appears.
- **Shade or annotate the important part**: drought periods shaded on a long time series (2021B-11552, 2021B-11576), optimal bands shaded on index plots (2023A-14632).
- **Prefer a table when exact values matter** and a figure when the pattern matters. Give both for headline forecasts.
- **Change a format when it does not work.** 2020A-11135 replaced a hard-to-read table with a graph in its app design (p. 24).

## Tables

- Keep tables small and focused; split a large table (2021B-11898 split monthly forecasts into Jan–Jun and Jul–Dec).
- Use consistent metrics across comparison tables (2018B-8506 used the same error measures in every comparison).
- Put the key row or column first, and bold or color the result the reader should notice.
- For rankings, show the score as well as the rank, so the reader sees the gaps.

## Equations

- **Number every displayed equation** and refer to equations by number.
- **Introduce, display, then explain.** After each equation, say in words what it means, why it has this form and what each new symbol is. 2024B-15022 printed a symbol glossary directly under its final model (p. 23).
- **Build up gradually.** Add one factor at a time with a new numbered equation (2018A-8744, Eqs. 5.1–5.7).
- **Show a substitution with real numbers** for at least one case (2021A-11462 did this inside its equations, pp. 8–9; 2023A-14076 wrote each species' score as an explicit sum).
- **Say the optimization direction** explicitly (minimize or maximize), and make sure the notation matches (see the arg max note in 2021A-11931).
- Use proper math typesetting; do not paste equation images of low resolution.

## Worked examples

A worked example is among the most valuable devices in the corpus. Take one realistic case (one persona, one battery, one plant, one city) and trace it through every step with actual numbers, then summarize the remaining cases in a table:

- 2020A-10549 took one persona through every step before summarizing the other nine (pp. 10–16).
- 2021A-11931 traced the Tesla Powerwall 2 through every equation (pp. 17–19).
- 2020A-10550 showed one sub-matrix column with its comparison matrix and eigenvector (pp. 12–13).
- 2014A-5086 built its recommendation around a standard 600-passenger train of 10 cars with 12 rows (p. 2).
- 2018A-8992 showed one imputation in full "in the interest of clarity" (p. 8).

## Pseudocode and algorithms

For simulations and search algorithms, give numbered steps or pseudocode in the body (2023A-13643, pp. 9–10, 20; 2021B-11552 numbered the Box–Jenkins steps), and put the full code in the appendix. A reader should understand what the code does without reading it.
