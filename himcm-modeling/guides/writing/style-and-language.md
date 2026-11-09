# Style and language

## Voice and tone

- **"We" is normal and natural.** Nearly every paper in the corpus writes "we assume", "we define", "our model". Use it consistently.
- **Confident but calibrated.** State results plainly, and qualify them exactly as much as the evidence requires. "The model predicts a 2050 level of about 960 ft under current trends" is better than both "Lake Mead will reach 960 ft" and "it may be possible that the level could perhaps decrease".
- **Formal, not stiff.** Occasional lively touches worked when they helped the reader: section titles such as "The Way Of The Wind" (2023A-14632); "Intuitively, the user does not care about the temperature when he is not at home!" (2018B-8506, p. 21). Keep these rare and keep the technical sections precise.
- **Plain words over impressive ones.** "Use", not "utilize"; "shows", not "demonstrates the efficacy of".

## Sentence patterns that do work

Adapt the pattern, not the words. All examples are from Outstanding papers.

**Defining a term or the goal**

- "We mean a best job for high school students as a job offering great gains, matching students' preferences, able to be completed by high school students, and of course, having great chance for the student to own it." (2020A-10550, p. 3)
- "The higher the disparity, the less suitability of the battery for the household." (2021A-11931, p. 7)
- "The first variable reflects spread intensity and the second one reflects spread range." (2023A-13643, p. 6)

**Justifying a choice in one sentence**

- "The starting time of the requested one-year period for the problem may influence the results because of seasonality, thus should be restricted." (2023A-13719, p. 5)
- "We asked for the range as opposed to the singular optimal level in order to account for the student's tolerance of deviations from his/her optimal amount." (2020A-11135, p. 11)
- "Given that the Top500 list covers the most powerful systems currently, the impact of other high-performance computers with lower performance on the overall computational demand is negligible." (2024B-15502, p. 4)

**Explaining a design rule in plain terms**

- "In other words, if the job has a higher risk than the user is willing to endure, its total index is 0 and the job is thrown out of consideration." (2020A-10656, pp. 7–8)
- "In other words, a job that is well-rounded with regards to the flexibility factors will be rated higher than a job that excels in one factor but is poor in the others." (2020A-11135, p. 13)
- "This approach implies that a species offering greater benefits will be regarded as having a lesser negative impact." (2023A-14140, p. 17)

**Rejecting an alternative**

- "which is not sensible, since the average dispersal distance cannot be far below zero." (2023A-14076, p. 9)
- "Therefore, we decided not to include the EWM model in further calculation." (2021A-11900, p. 19)

**Reading a result**

- "This indicates that increasing the proportion of renewable energy has a clear mitigating effect on carbon emissions, but the growing demand for HPC remains the primary driver of future emissions." (2024B-15022, p. 18)
- "Dandelions have a relatively high ranking but are not among the top species. This is because dandelions are edible and have medicinal and culinary use, which lowers the global impact factor." (2023A-13643, p. 21)

**Being candid about a limitation**

- "Our model tends to overestimate the loss in water elevations for future timeframes if it's given an incomplete picture of the lake's hydrological cycle." (2021B-12384, p. 16)
- "Nest is superior to our learning algorithm in terms of transparency." (2018B-8506, p. 22)
- "Despite the limitations, we can still gain a general idea of how dandelions seeds should spread from this model." (2023A-14140, p. 5)

**Making a decision rule explicit**

- "we set a threshold of inclusion as 0.45, based on the distribution of the simulation results" (2024A-15926, p. 1)
- "By comparing RMSE, MAE and MRE, the exponential model has the best performance in the training set and test set, and is the most accurate." (2022B-12646, p. 1)

**Explaining a result to the client**

- "Under the specific annual funding column, the number corresponding to a project indicates the start year of the project." (2020B-10997, p. 23)

**Turning results into guidance**

- "Normal distribution is recommended if a predominant wind direction is evident, while uniform distribution is more appropriate for more random wind directions." (2023A-14076, p. 24)

## Habits to avoid

- **Claims without support.** "Our model is highly accurate" with no error measure; "validating the accuracy and feasibility of the model" after one rough comparison. Say what was compared and how close it was.
- **Presenting a screening score as a prediction.** A threshold on a constructed score says which options pass your rule, not what a committee will decide; the stronger 2024A papers kept that distinction (2024A-15926 treated 0.45 as an inclusion threshold for its score).
- **Over-claiming from limited tests.** Agreement with self-generated data, a handful of personas or one external figure supports plausibility, not proof.
- **Method lists without reasons.** "We used AHP, entropy weights, TOPSIS and k-means" tells a reader nothing about why.
- **Vague quantities.** "A large increase", "hundreds of millions of tons" where a number with a range is possible (see the 2024B-16226 card).
- **Inconsistent terms.** Call each thing by one name throughout. If the model is called the "Battery Ranking Model" in section 3, it is not "our evaluation system" in section 6.
- **Inconsistent numbers.** One value for each result in the summary, body, conclusion and memo.
- **Padding.** Long background, restating the problem twice, or explaining standard methods at textbook length. Explain what is specific to your use instead.
- **Unlabeled jargon.** Define every technical term and acronym at first use.
- **Long, nested sentences.** Split them. One idea per sentence in the technical sections.

## Language mechanics

- Keep tense consistent: present tense for what the model does and what results show ("the model predicts"), past tense for what the team did ("we collected").
- Write numbers with sensible precision. A forecast stated as 1,034,015.58 dollars implies more precision than the model has unless it is an exact sum; round to what the inputs support, except where an exact figure is the point.
- Give units everywhere, including in tables and axis labels.
- Spell-check, and read the paper aloud once. Many papers in the corpus have small grammar errors; they rarely sink a paper, but clean writing makes every argument easier to follow.
