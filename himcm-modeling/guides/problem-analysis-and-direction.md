# Reading the problem and choosing a direction

This guide covers the first hours of a contest: understanding the problem, deciding what the paper will be about, and planning the work. It draws on how the Outstanding teams read their problems (the "How they read the problem" section of each paper card). The examples show moves that worked, not steps you must copy.

## 1. Read the statement as a contract

- **List every requirement and sub-requirement** (1a, 1b, 2, ...) with its exact verb: "list", "develop a model", "test", "discuss", "recommend", "write a one-page letter". Each one needs a clearly labeled answer in the paper. Many strong papers put a requirement-to-section table in the introduction (2024B-15502, p. 3) or tag headings with the requirement they answer ("(For question 1a)", 2020B-10876, p. 5).
- **Note the deliverables and the format rules**: page limit, summary sheet, table of contents, references, and any memo, letter, article or app page. These come from the current statement, not from past papers.
- **Take the wording seriously.** Several teams gained a clear angle simply by answering what the statement actually said:
  - 2020A asked for factors that are "deterministic or probabilistic". 2020A-10701 used expected values for overtime pay and hours (pp. 6, 8).
  - The 2023A title was "Friend? Foe? Both? Neither?". 2023A-14632 kept harm and benefit as two coordinates instead of one number, and distinguished "foreign" from "invasive" as the glossary warned (pp. 13–14).
  - "Long-term and reliable" funding became an explicit objective of a smooth yearly budget in 2020B-10839 (p. 4).
- **Check the statement and data for errors or ambiguities**, and say how you resolve them. 2022B-12465 opened by showing that a data set described as March means was actually annual means (pp. 3–4). 2023A teams had to decide when the puffball appears and where the parent plant sits; 2023A-13643 searched over all twelve starting months (p. 11), and 2023A-13719 fixed a per-hemisphere year with a stated reason (pp. 4–5).

## 2. Define the key word before choosing a method

Most HiMCM problems hinge on an undefined word: "best", "impact", "drought", "reliable", "realistic". The single most common feature of the strong papers is a one-sentence definition, stated early, that the model then computes.

| Problem | Undefined word | How a strong paper defined it |
|---|---|---|
| 2018A roller coasters | best | net experience = thrill minus discomfort, so extreme specifications are not automatically best (2018A-8744, p. 14) |
| 2020A summer job | best | gains + preference match + feasibility + the chance of actually getting the job (2020A-10550, p. 4) |
| 2021A batteries | best | lowest cost to meet the worst case (2021A-11462); best weighted attributes (2021A-11900); least shortfall from the household's needs (2021A-11931) |
| 2021B Lake Mead | drought | a level below the supply-critical 1115 ft (2021B-11576, p. 13); hydrological drought only, because only that is visible in elevation data (2021B-12384, p. 10) |
| 2023A dandelions | impact factor | a 0–5 harm score where benefits lower the score (2023A-14140, p. 3); a harm/benefit pair (2023A-14632) |

The 2021A problem card shows three different definitions of "best" leading to three different but equally Outstanding answers. **Clarity about the definition mattered more than which definition was chosen.**

## 3. Find the structure of the problem

Ask what kind of problem this is underneath the story. Strong papers often reframed the story into a standard structure, which then suggested the method:

- **Choice among options** (summer jobs, batteries, coasters) → multi-criteria evaluation. Decide which criteria are hard constraints and which are trade-offs (2020A-10656 multiplied 0/1 gates with soft penalties, pp. 7–10).
- **Allocation over time under a budget** (2020B conservation funding, 2023B e-bus transition) → scheduling or optimization. 2020B-10876 saw that delay is costly because feasibility falls while a species waits, which is what makes the schedule matter (pp. 3, 8–10).
- **Change over time** (CO2, lake level, market share) → regression, time series or differential equations. Ask whether the system has a mechanism (a water budget, a market equilibrium) or only a trend.
- **Spread in space and time** (dandelions, drones) → simulation with explicit rules. Separate "how many" from "where" (2023A-14076 used a Leslie matrix for numbers and Monte Carlo for positions, p. 8).
- **An unmeasured quantity** (global HPC energy) → build a proxy and state it as an assumption (2024B-15022 used data-centre plus crypto-mining energy, p. 4; 2024B-15502 built it bottom-up from machine specifications, pp. 3–6).

Also look for **the hidden half of the problem**. In 2021A the battery choice only made sense once household demand was estimated; in 2019B-9548 the teams saw the drinks market as the root cause of every impact the statement listed (pp. 1, 5).

## 4. Let the data shape the plan

- **Go through the given data column by column**: what each field means, its units, how much is missing, and what it can and cannot support. 2018A-8700 did this field by field and gave reasons for every dropped variable (pp. 7–8); 2020B-10839 mapped each data column to a factor (pp. 3–4).
- **Look before modeling.** Correlations, outliers, missing-value patterns and plots of the raw data often decide the method. 2018A-8744 dropped drop height in favor of height (r = 0.95, and drop was 53% missing) and replaced inversion count with inversions per second (pp. 10–12).
- **If the problem gives little or no data**, decide early what you will collect, from where, and what you will assume instead. Name sources (government statistics, published studies, manufacturer specifications) and plan to vary the assumed values in a sensitivity analysis.
- **Scope by what the data can support, and say so.** 2019B-9548 left job losses and emergency costs out of the numbers for lack of data, but kept the formulas ready "if the data is given to us" (p. 18).

## 5. Choose the scope deliberately

Every strong paper narrowed the problem in a stated way: a time window, a geography, a type of user, a definition. Good scoping sentences give the choice and the reason together:

- "The only droughts that could be adequately described with water elevation data are hydrological droughts." (2021B-12384, p. 10)
- 2024B-15022 used twenty countries to stand in for the global total, each facility using its host country's energy mix (p. 4).
- 2023B-13694 counted only costs "directly incurred by the city" (p. 13) and represented each bus type by one specific 40-foot model to control for size (p. 4).

Scope too narrow and you answer a different problem; too broad and nothing gets done well. If a narrowing changes the answer, test it in the sensitivity analysis.

## 6. Where new and interesting directions came from

In this corpus, novelty rarely meant an exotic method. It usually meant **one well-motivated twist on a sound core**: a realistic feature of the situation that the statement implied but did not spell out, built into the model. Examples:

- **The chance of getting the job** as part of "best" (2020A-10550).
- **Net pay after commuting and meals, and a 12-hour day as a recreation budget** (2020A-10701).
- **Ideal-point preferences**: for social interaction or physical activity, more is not always better, so the student's preferred range became a bell curve (2020A-11135, pp. 11–12).
- **Real users make mistakes**: an algorithm that repairs or points to inconsistent AHP judgments (2020A-10549, 2020A-11135).
- **Learning the user's own routine** instead of assuming a 5+2 week (2018B-8506, p. 7).
- **Delay has a price** in a funding schedule (2020B-10876).
- **A community's right to energy** as the socioeconomic extension (2024B-15502, p. 19).
- **Two kinds of user**: a general ranking and a personal one on a shared base (2018A-8992).

To find your own twist, ask:

- Who uses the result, and what do they actually need to decide?
- What does the statement assume away that a real decision-maker would care about?
- Where would a simple model give an obviously wrong answer, and what would fix it?
- Can one framework answer all the requirements? 2023B-13694 modeled one bus of each type over its life and scaled up to fleets and cities (p. 4); 2019B-9548 used one market model for town, city and airport by changing parameters (p. 6).

Check every idea against three questions: Does it answer a requirement better? Can you get data or a defensible assumption for it? Can you finish it in the time available? An original idea that is not finished or not explained does more harm than good.

## 7. Turn the direction into a plan

Before modeling, write a one-page plan. Several papers printed a version of it as an "Our work" flowchart or a "Problem analysis" section (2017A-7359, pp. 5–7; 2022B-12465, pp. 4–5; 2021B-11576, Fig. 1).

| Requirement | Question in our words | Approach and model | Data / assumptions needed | Output (number, table, figure) | Check (validation or sensitivity) | Owner |
|---|---|---|---|---|---|---|
| 1a | ... | ... | ... | ... | ... | ... |

Also decide early:

- **The thread through the paper**: the definition, the scenario pair or the framework that every section will use. 2024B-16226 kept one scenario pair from the model through to the letter.
- **How parts connect.** Strong papers reused Part 1 outputs as Part 2 inputs (2023A-13719 and 2023A-14140 fed their spread simulations into the impact factor) and sized the plan with the forecast (2021B-11576, p. 20).
- **What will be cut if time runs short**, so the core requirements are always answered.
- **When writing starts.** The summary sheet, memo or article and the final checks need real time; see [writing/](writing/README.md).

## 8. Habits to avoid

- Choosing a method first and then looking for a problem it fits.
- Choosing a method only because a past paper used it, or rejecting one only because none did.
- Leaving the key word undefined, or defining it differently in different sections.
- Answering an easier question than the one asked (for example, showing that CO2 rises when the question asks whether the recent rise is faster than before; see the note in 2022B-12465).
- Silent scoping: narrowing the problem without saying so or why.
