<div class="ai-report">

# Report on Use of AI Tools

*This report is not counted toward the 25-page limit.*

Our team used AI assistants throughout the project. All final choices of definition, criteria and the five preference statements P1–P5 were reviewed and confirmed by the team; every number in the paper was produced by code that the team can rerun from archived public data.

| # | Tool | How we used it | What we did with the output |
|---|---|---|---|
| 1 | OpenAI ChatGPT / Codex (local agent with sub-agents), Nov. 2026 | Searching for and downloading public datasets for 25 cities (Census, CRDC, EDFacts, FBI, FARS, EPA, SAMHSA, NTD, HUD, BEA, IMLS, HRC, fare and wage pages); writing collection, cleaning and archiving scripts; recording access failures | Checked file hashes, row counts and coverage tables; kept failed downloads as documented gaps instead of filling them |
| 2 | Anthropic Claude, used through Claude Code (cloud sessions), Nov. 2026 | Reading 92 Outstanding-paper analysis cards and the HiMCM writing guides; proposing model structures; writing the model code (indicator matrix, floors, piecewise-linear value model, linear programs, SMAA, regret, ELECTRE III, sensitivity, figures); auditing data; drafting this paper and the news article | Ran all code ourselves; verified LP bounds against 3,000 sampled weight vectors, hand-checked one city's score, compared rerun results with stored results; reviewed and edited the text and chose the final definition and preference statements |

**Representative prompts (paraphrased).**

1. "Collect the most recent public data for the 25 largest U.S. cities on high-school course access, school support staff, crime, traffic deaths, air quality, youth mental-health services, transit, parks, libraries, wages, rent and non-discrimination policy; record sources and gaps." → datasets, scripts and a gap log (tool 1).
2. "Read the knowledge-base paper cards and propose a model that ranks cities without letting low rent compensate for safety, and that shows how robust the ranking is to different weights." → the floors + piecewise value + LP + SMAA design (tool 2).
3. "Build the indicator matrix from the archived data and run all models; audit any measure that looks wrong." → code and the two real-data revisions in Section 7 (tool 2).
4. "Write the full paper and a one-to-two-page news article from the results files, following the HiMCM page limit and the writing guides." → the draft of this document; every number in it was checked against the results files (tool 2).

**Limits we observed.** The AI tools sometimes proposed weaker choices that we corrected after checking: an initial ELECTRE veto threshold that vetoed almost every comparison, a sampling loop that ran out of memory, and a sentence that misdescribed course enrollments as a share of seats. None of these errors remains in the results.

</div>
