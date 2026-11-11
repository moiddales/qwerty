# 交接文档：HiMCM 建模知识库

## 当前工作更新：2026-11-11

最新进度（A-002）：已完成 [A 题数学模型分析](projects/himcm2026A/MATH_MODELS.md)和构造例子核验，研究方案与项目交接已同步更新；尚未产生真实城市排名。

当前在本知识库基础上开展 2026 HiMCM A 城市选择研究。接手先读根目录 [AGENTS.md](AGENTS.md)、[项目日志](PROJECT_LOG.md)与 [A 题交接](projects/himcm2026A/HANDOFF.md)，当前方案在 [PLAN.md](projects/himcm2026A/PLAN.md)。

用户新增持续规则：每次重大修订都必须提交并推送到 claude/affectionate-mayer-ihqczh，同时记录用户要求原文、日期、具体改动和待办，假定会话随时丢失。该规则已写入 AGENTS.md。

知识库 92 篇论文卡和 22 张题目卡的建设已完成。下方 2026-11-08 的缺项清单是历史记录；当前 A 题任务按独立项目交接继续，不据该旧清单重做语料工程。

接手的 AI 请先完整读完本文件再开始工作。前一个 AI 的对话上下文你看不到，项目背景、用户的全部指令、当前进度、剩余工作和工作规范都写在这里。

- 仓库：`moiddales/qwerty`（私有）
- 工作分支：`claude/affectionate-mayer-ihqczh`，所有提交都推送到这个分支
- 交接日期：2026-11-08
- 状态更新（2026-11-09）：接手的 AI 已完成全部 92 张论文卡和 22 张题目卡，已合并入仓库。下文第 3、4 节是交接当时的状态，仅作记录。

---

## 1. 项目是什么

用户所在机构的作者授权了一份 PDF，是 2014–2024 年 HiMCM 的 Outstanding（特等奖）论文合集：2,973 页，92 篇论文，每篇都经 COMAP 官方结果核实为 Outstanding，其中 12 篇另获 NCTM 奖。

用户要用它在 GitHub 仓库里建一个 HiMCM 数学建模知识库（Claude skill，人类也能读），帮助：

1. 选择研究方向；
2. 做研究和数据分析，包括常用模型；
3. 写论文（最重要）：体裁、风格、要做什么、要避免什么。

---

## 2. 用户的全部指令（按时间顺序，原文照录）

> 下面引号里是用户原话；"说明"是前一个 AI 的执行记录或理解，"状态"表示这条指令现在是否还有效。

1. 「我绑定了dropbox的连接器，我在dropbox里面上传了一份pdf文档，dropbox只有一个文件，200MB左右，帮我下载到你的工作空间，我批准你执行各类需要的操作而不需询问我同意」
   - 状态：已完成。原始合集 PDF 不在仓库里，仓库里只有拆分后的 92 份单篇 PDF；需要原件时可以重新从 Dropbox 下载。
2. 「如何验证邮箱，我没有看到提示」「验证好了」
   - 说明：Dropbox 连接器要求验证邮箱，已解决。
3. 主需求，后续一切工作都以这条为准：
   - 「这个pdf是我们机构的作者们给我授权的历年HiMCM论文范文，我需要用这个文档里的内容建设一个HiMCM建模研究使用的知识库（skill—，用于提升AI研究和数学建模的效率，细节如下：1.这个知识库需要整理汲取过往论文的经验，包括确定研究方向时，可以参考过往论文是怎么确定方向的，研究方向是什么，如何有新意的研究方向，如何指定研究方案…2.在执行研究和数据分析时，要做什么，有哪些常用的数学模型。3.（最重要）在论文写作时，论文的体裁，风格应该如何，需要注意什么，需要避免什么……。以上的内容只是可选项而不是完整详尽的例子。我需要你先读一下文档内容，确定一个构建方案。我需要注意以下几点，1.使用github仓库搭建知识库。2.需要避免这个知识库或者skill导致AI死板地只是照用原来的经验（例如“过去论文没有用过这个模型，因此我不能用这个模型”）—这些论文并不一定百分之百正确或者完美或者符合要求。3.需要未来可以加入更多论文进行扩展。4.AI每次都要读取完整PDF可能会增加不必要的token用量和时间，在绝对不牺牲资料准确性的情况下减少成本浪费，但是准确性和性能的优先级仍然远远高于成本。」
   - 状态：长期有效。
4. 「先去尝试下载题目原文」
   - 状态：已完成。2014–2025 年所有题目原文和附件都在 `sources/problems/`。2017B 和 2020B 的附件在网上已找不到。
5. 「评估平行精读的成本，我不想要使用Haiku或者sonnet之类更弱的模型。平行精读是否比你在一个主对话里面全部读完成本更低（我可以设置500k，800k……自动压缩上下文）」
   - 状态：长期有效的部分是**不要用 Haiku、Sonnet 等更弱的模型**。
6. 「帮我查一下opus5.5的有没有长上下文额外计费」
   - 说明：查到 Opus 5.5 的价格是每百万 token 输入 $4、输出 $20，缓存读取按 0.05 倍计价，没有长上下文附加费，上下文 1M。
7. 计划修订指令，长期有效：
   - 「1.允许就用这个仓库，我查过了它是私有的。2.语言可以全部用英文。3.可以放原始PDF，4.注意，这个项目不只是给AI使用的，人类也可以使用，你不需要把“披露xxx”政策写进知识库的写作指南和自查清单。这对人类读者无意义，对AI来说可能导致在不是AI声明的地方加入有问题的内容。相反，我要你给我一个md文件用来单独发给AI提醒，因此md文件不需要放到知识库。5.我需要你避免找茬式罗列每一个论文的问题，主要还是参考优点，既然它们都是特等奖说明其有很多可取之处。6.你可以适当让一个子代理阅读更多论文，仅仅只在这可以提升准确性和质量的前提下。现在重新修改确认执行计划。」
   - 说明：第 4 点提到的提醒文件附在本文件附录 A，请保持它不进入 `himcm-modeling/`。第 6 点后来被第 14 条覆盖。
8. 「注意 我只要你给计划，还不需要开始任务」
   - 说明：用户确认计划之前不要开工。
9. 用户用 /goal 设定的目标：「确认计划，现在按照以上计划完成完整工作。注意子代理使用opus5.5（不是opus5或者其他更旧的模型）」
   - 状态：模型要求长期有效。如果用子代理，只能用 Opus 5.5（`claude-opus-5-5`）。
10. 「继续原有计划且不要中断，核查部分使用opus5.5抽查，你自行决定抽查比例，我需要节约成本。」
11. 「注意，你刚刚跑了以下项目立刻把我五小时额度几乎用光了紧急分析，但是不要浪费目前已经的沉没成本」
    - 说明：前一个 AI 一次并行开了约 20 个子代理，几乎耗尽用户的 5 小时额度。
12. 「之后项目一次最多并行三个子代理」
13. 「紧急停止所有子代理，不要再消耗额度了」，之后又说「继续，最多平行使用三个子代理」，以及「分析额度用量，额度消耗太快了」
14. 「目前子代理结束之后剩下所有项目都不使用子代理，你来读」
    - 状态：这是关于子代理的最新指令，目前有效：**不要使用子代理，所有阅读都在主对话里自己做**。如果用户以后改口，以新指令为准；即便放开，也最多 3 个并行，并且只用 Opus 5.5。
15. 用户清除了 /goal，然后说「完成目前进度后保存停止任务」
    - 状态：已执行。
16. 「现在收尾知识库搭建项目，不要再读新的论文了」
    - 说明：前一个 AI 据此停止读论文，只用已有的卡片写完了指南、入口文件和文档。这条是针对那次收尾说的。接手后要不要继续读剩下的论文、写卡片，**请先向用户确认**。
17. 「现在我需要让另一个AI接手剩下的内容，帮我写一个交接文档，另一个AI没有你的上下文，所以交接文档需要包括我的全部指令」
    - 说明：也就是本文件。

### 从以上指令归纳出的长期规则

- 知识库内容全部用英文，人类和 AI 都要能用。
- 防止 AI 死板照搬：语料只说明"这样做行得通"，不说明"只能这样做"。论文不完美。不能因为"过去没用过"就排斥某个方法。
- 要可扩展，能随时加入新论文。
- 降低成本，但不牺牲准确性；准确性和性能远比成本重要。
- 以学习优点为主，不要找茬式罗列每篇论文的问题。
- 知识库（`himcm-modeling/` 下的指南、清单、卡片）里**不写任何 AI 披露或 AI 工具相关内容**。
- 不使用 Haiku、Sonnet 等较弱模型；子代理只能用 Opus 5.5。当前不使用子代理。
- 用户很在意额度消耗：避免大批量并行，避免不必要的长输出和重复读取。

---

## 3. 当前进度

### 已完成

- **语料预处理**：
  - 92 篇论文拆分成单篇 PDF（`sources/papers/<ID>.pdf`）。
  - 逐页抽取全文（`himcm-modeling/corpus/papers/<ID>.md`，用 `## Page N` 标页，N 是该 PDF 的页码）。
  - 修复了私用区字符、small-caps、Symbol 字体、"ff" 连字被抽成 "↵" 等问题。
  - 扫描件 2024A-15504 已人工转写（`tools/manual_transcriptions/2024A-15504.md`）。
- **题目原文**：`himcm-modeling/corpus/problems/2014A.md` 至 `2025B.md`，附件在 `sources/problems/<年份>/`；COMAP 历年结果文件在 `sources/results/`。
- **卡片**：33 张论文卡（`himcm-modeling/papers/`），6 张题目卡（`himcm-modeling/problems/`：2018A、2020A、2021A、2021B、2023A、2024B）。
- **入口和指南**，全部基于这 33 张卡写成：
  - `himcm-modeling/SKILL.md`
  - `guides/problem-analysis-and-direction.md`
  - `guides/modeling-workflow.md`
  - `guides/model-catalog/`：README 加 4 个方法族文件
  - `guides/writing/`：6 篇
  - `guides/review-checklist.md`
- **人类文档**：仓库根目录的 `README.md` 和 `CONTRIBUTING.md`（加论文的流程和卡片模板）。
- **工具**（`tools/`）：`check_cards.py`、`build_index.py`、`ingest.py`、`render_page.py`、`build_problem_texts.py`、`split_booklet.py`、`textclean.py`、`corpus.py`。
- **校验**：`python3 tools/check_cards.py` 当前 0 错误。它会检查卡片字段和章节、页码范围、引文是否逐字出自原文，以及指南里的论文编号、页码和链接。
- **2025 年题目测试**：用 2025A/B 走了一遍使用流程，发现关于路径规划、选址和足迹核算的指导不足，已经补上。

### 各题卡片完成情况

| 题目 | 论文卡 | 缺少的论文卡 | 题目卡 |
|---|---|---|---|
| 2014A Unloading Commuter Trains | 0/5 | 4671, 4813, 4823, 5086, 5089 | 无 |
| 2014B The Next Plague? | 0/4 | 4637, 4880, 5295, 5325 | 无 |
| 2015A Preventing Road Rage | 0/4 | 6057, 6080, 6083, 6117 | 无 |
| 2015B City Crime and Safety | 0/4 | 5473, 5967, 6018, 6129 | 无 |
| 2016A Swim, Bike, and Run | 0/4 | 6453, 6770, 7054, 7055 | 无 |
| 2016B Shop and Ship | 0/5 | 6475, 6829, 7037, 7057, 7211 | 无 |
| 2017A Drone Clusters | 1/5 | 7879, 8028, 8040, 8393 | 无 |
| 2017B Ski Slope | 0/3 | 8121, 8124, 8201 | 无 |
| 2018A Roller Coaster | 5/5 | - | 有 |
| 2018B Cozy Smart House | 1/2 | 9247 | 无 |
| 2019A Charge! | 0/5 | 9564, 9824, 9844, 10057, 10174 | 无 |
| 2019B Bottle Battles | 1/4 | 9869, 10337, 10407 | 无 |
| 2020A The Best Summer Job | 5/5 | - | 有 |
| 2020B Funding Biodiversity Conservation | 2/3 | 10997 | 无 |
| 2021A Storing the Sun | 3/3 | - | 有 |
| 2021B Tackling the Drought | 5/5 | - | 有 |
| 2022A The Need for Bees | 0/4 | 12600, 12821, 13014, 13405 | 无 |
| 2022B CO2 and Global Warming | 1/5 | 12646, 12678, 12911, 13010 | 无 |
| 2023A Dandelions | 5/5 | - | 有 |
| 2023B Charging Ahead with E-buses | 1/4 | 13904, 14087, 14323 | 无 |
| 2024A Modeling Future Olympic Games | 0/5 | 14995, 15041, 15504, 15926, 16159 | 无 |
| 2024B Environmental Impact of HPC | 3/3 | - | 有 |

论文 ID 的格式是"年份+题号-队号"，例如 `2014A-4671`。目前一共还缺 59 张论文卡和 16 张题目卡。用 `python3 tools/build_index.py` 生成的 `himcm-modeling/catalog.md` 末尾有完整列表。

---

## 4. 剩余工作（开始前先和用户确认范围，见第 2 节第 16 条）

1. **复核未核完的卡片。** 这些卡片的写作子代理在复核途中被用户叫停，卡片已写完且通过了自动检查，但没有做完人工对照原文的复核：
   - 2018A 的 5 张论文卡和 2018A 题目卡；
   - 2020A-10701 和 2020A-11135。

   另外，其余卡片只做过自动检查，以及少量 Opus 5.5 抽查。用户要求核查以抽查为主、节约成本，抽查比例由 AI 决定。
2. **补写剩余论文卡**（上表），优先补齐已经部分完成的题组：2020B-10997、2018B-9247、2017A、2019B、2022B、2023B。然后是完全没开始的组。
3. **每组论文卡写完后写该组题目卡**，格式见 `CONTRIBUTING.md` 和 `problems/2020A.md`。
4. **用新证据更新指南**：新卡片里出现新的有用技巧、结构或写作手法，或推翻原有建议时，修改 `guides/`，引文按 `"..." (<ID>, p. N)` 的格式写，方便检查器核对。不要因为某种方法出现得多，就把指南写得更窄。新的题目类型（比如 2014A 的排队、2014B 的传染病、2016B 的物流、2024A 的奥运项目评估）可能需要在 `model-catalog` 里补例子。
5. **每完成一组就检查、重建索引、提交并推送**：
   ```bash
   python3 tools/check_cards.py
   ```
   ```bash
   python3 tools/build_index.py
   ```
   ```bash
   git add -A && git commit -m "..." && git push -u origin claude/affectionate-mayer-ihqczh
   ```
6. **全部完成后，更新 `README.md` 和 `SKILL.md` 里的覆盖率说明**（目前写的是"33 张论文卡、6 张题目卡"）。
7. 不要创建 Pull Request，除非用户明确要求。

---

## 5. 写卡片的规范

完整模板和流程在 `CONTRIBUTING.md`，`check_cards.py` 里有字段、章节和方法族受控词表（`FAMILIES`）的定义。下面是前一个 AI 给阅读者的规则摘要，必须遵守：

- **读全文。** 摘要页、正文、信件/备忘录/新闻稿、参考文献都要读完整；代码附录和原始数据表可以略读，但要记下用了什么语言和工具。
- **按需渲染 PDF 页面。** 文字抽取会丢失图片、弄乱公式和表格。关键图、结果表、摘要页版式、驱动模型的公式看不清时，渲染该页查看：`python3 tools/render_page.py <ID> <页码>`，或用 `pdftoppm -r 110 -f N -l N -png sources/papers/<ID>.pdf <临时目录>/<ID>-p`。要有选择，通常每篇 2–6 页，图多的论文可以多看几页。渲染的图片不要放进仓库。全文里标着 "[no extractable text on this page: image only]" 的页（常常是备忘录或文章）只能这样看。
- **立场。** 以优点为先，具体说明这篇论文值得学什么：怎么理解题目、哪些建模选择有效及原因、怎么验证，尤其是怎么写和怎么呈现。
- **不找茬。** 不列错别字和小毛病。"Notes for reuse" 只写 0–3 条确实会误导模仿者的问题，用建议的口吻写；没有就写 "None noted."。
- **描述，不立规矩。** 某篇用了模型 X，只说明 X 可以用于这类问题，不说明必须用 X。
- **忠实。** 不编造结果、数据来源、动机或数字。论文没说为什么，就写 "rationale not stated"。区分论文说的和你自己的解读。
- **引文。** 必须逐字，加引号并标页码 `(p. N)`，页码用 PDF 页码，不用论文里印的页码。每条最多两句，每张卡最多约 5 条。
- **不提 AI。** 不提 AI 工具、AI 政策或 AI 披露。
- **篇幅。** 论文卡约 1,000–1,600 词，题目卡约 1,000–1,800 词。过长会增加成本，以前子代理写的卡常超过 2,000 词。
- **复核。** 每张卡写完后对照全文复核一遍：所有事实、数字、模型名和页码都要正确。
- **已知语料问题：**
  - 2021B-11823 超过页数限制（33 页）；
  - 2023A-14140 有 27 页，含附录；
  - 2024B-16226 的部分数据是代码随机生成的，卡片里已注明；
  - 2018B-8506 有 67 页，2020 年以前没有 25 页的限制。
  - 约 204 个无法恢复的字形显示为 U+FFFD。

---

## 6. 成本与效率要点（用户非常在意）

- 一次开 20 个子代理会在短时间内耗尽 5 小时额度。现在规定不用子代理；即使将来放开，也最多 3 个并行。
- 主要消耗来源有这些，应当避免：
  - 大批量并行；
  - 卡片写得过长；
  - 渲染过多图片；
  - 缓存过期后重新唤起子代理；
  - 主对话上下文过大。

  上下文变大时，可以提醒用户运行 `/compact`。
- 读论文时一篇一篇读全文，写完一组就提交，避免进度丢失。

---

## 7. 环境说明

- 如果是全新容器，可能需要安装 poppler-data（中文 CID 字体映射），命令是 `apt-get install -y poppler-data`。另外需要 `pdftotext`、`pdftoppm` 和 Python 包 `pypdf`。
- 已经停止的工具调用不要重复执行；`sources/` 下的文件很大（约 220 MB），不要无谓地复制。
- 工具都从仓库根目录运行。
- 提交信息按你所在环境的署名要求写。不要在提交、PR 或仓库文件里写模型版本号。

---

## 附录 A：单独发给 AI 的提醒文件（用户要求不放进知识库）

用户要求写一份单独发给 AI 的 md 文件，提醒 COMAP 的 AI 使用政策，并明确要求这份文件不放进 `himcm-modeling/`。原文件在前一个会话的临时目录里，会随会话结束丢失，所以完整附在下面。如需单独使用，复制出来另存即可；不要把它的内容写进知识库的指南、清单或卡片。

````markdown
# Reminder for AI assistants helping a HiMCM team

Read this before assisting a team that is preparing a HiMCM/MidMCM submission. It summarizes COMAP's policy "Use of AI Tools in COMAP Contests" (version v102025, linked from the HiMCM problems page) and tells you how to behave so the team stays compliant. If the policy and this note ever disagree, the policy wins; ask the team to check the current version on the COMAP site.

## What the policy requires of the team

- Responsible use of AI is permitted, but every use must be disclosed. This covers LLMs, generative AI, math software with AI features, translation tools, code copilots and auto-complete.
- Disclosure has three parts, all decided and written by the team:
  1. Inline citations where AI-produced material is used.
  2. The AI tools listed in the reference section.
  3. A separate section titled **Report on Use of AI Tools**, placed after the end of the solution report. It has no page limit and does not count toward the 25-page solution. For each tool: name and version/date, and for non-translation uses the exact query and the complete output. For translation, a short statement of what was translated is enough.
- The submission form also asks for an AI use statement (Yes/No).
- The team must verify the accuracy of everything an AI produced, including every citation, and must check that AI output does not reproduce someone else's text.
- COMAP takes action against submissions that used AI without disclosure.

## How you should behave

1. **Do not write disclosure text into the solution on your own.** Do not add AI acknowledgements, "generated with AI" notes, AI citations or remarks about yourself to the summary sheet, the body, the letter/memo or the references unless the team explicitly asks you to draft them. Where disclosure goes and what it says is the team's decision.
2. **Help the team keep a usage log.** When the team asks, or at the end of a substantial working session, offer a short log entry: tool and version, date, what it was used for, and the query and response (or where they are saved). The team needs exact queries and complete outputs for the Report on Use of AI Tools, so suggest they save conversations as they go.
3. **Never fabricate.** Do not invent data, statistics, sources, quotations or references. Mark any number you estimate as an assumption and say how it was derived. If you cannot verify a source, say so plainly.
4. **Do not copy published papers.** Past Outstanding papers (including any in a reference library you were given) are for learning approaches and techniques. Never paste their sentences, tables or code into the team's solution; help the team express their own work in their own words.
5. **Keep the team in charge of the modeling.** COMAP advises caution when AI is used for model selection and building, code, interpreting results and drawing conclusions. Explain your reasoning, present alternatives with trade-offs, and make sure the team understands and can defend every choice. Do not hand over a finished solution.
6. **Respect the format limits.** In recent contests (2024–2026) the 25 total pages include the summary sheet, table of contents, solution, letter/memo and references list; only the Report on Use of AI Tools is excluded. Check the current year's problem statement, which lists exactly what counts.
````
