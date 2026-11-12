# 用户清单审计（10 项）

> **状态（2026-11-12）：已全部应用到正式论文**（提交 e495e1b 及之后）。用户决定：交通死亡底线删除、加 P6"安全 ≥ 1/7"、Chicago 犯罪改用约 960 的口径；模型据此重跑，论文里的数字已全部换成新结果，所以本报告中引用的旧数字（如 Seattle 63.6%）只代表审计当时的模型。清单审计的英文替换文本按新结果做了相应调整后写入论文。

日期：2026-11-12。对象：用户截图中的 10 条清单。每一项都先在 `paper/paper.md` 中定位原文，再核对代码、数据或外部事实，最后给出结论和可直接替换的英文文本。正式论文**没有修改**。

新增的计算都可以复现：
- `analysis/model/run_checklist_checks.py` → `results/checklist_checks.json`（把原来只在参考权重下做的检验放到 $\Theta_S$ 下重跑；安全权重陈述；Chicago 犯罪口径）
- `analysis/model/run_nhts_teen_mode.py` → `results/nhts_teen_mode.json`（全国青少年出行方式）

## 总表

| # | 清单原文（摘要） | 结论 | 是否改变结果 |
|---|---|---|---|
| 1 | 不需要强调可负担性和包容性分开 | **同意**。分开是建模时的内部要求，正文里强调它对读者没有信息量。删两句即可 | 否 |
| 2 | "without a car"意义不明 | **同意**。概念有数据支持，但论文没给定义；而且 9.1 节另设了一个"Student without a car"画像，和主模型的假设重复，读者会更困惑 | 否（画像改名需重画图 6） |
| 3 | 1.2 "低租金不能买回危险街道"例子不好 | **同意**。现实中确实有人为了低租金住在危险地区，这个例子和常识冲突。改用论文里实际有的指标 | 否 |
| 4 | 底线各项（如交通安全）是否真的合理 | **四条里只有房租底线理由充分**。暴力犯罪和交通死亡两条底线没有外部依据，在点估计下也从未生效；交通死亡尤其不像"不能被补偿的需求"。建议去掉交通死亡底线或改写理由 | 去掉交通底线：任何城市的状态都不变 |
| 5 | 3.2 大学排名的理由不合理 | **同意，并已核实**。公立大学确实偏向本地学生，但按"州"和"每所高中"计算，不按城市计算；私立大学面向全国招生。所以"本市有好大学"不等于"本市高中生更容易上好大学" | 否 |
| 6 | 3.3 "consolidated 'balance'"什么意思 | 已核实含义（见下）。我们所有数据用的都是 balance 边界，口径一致；原文太简略，需要改写 | 否 |
| 7 | 5.4 "安全 vs 活动"的例子不好 | **同意**。换成确实有分歧的一对。但这条也暴露了第 9 项的问题 | 否 |
| 8 | 参考向量 θ⁰ 用在哪里、是否只是参考、说清楚了没有 | **没说清楚**。θ⁰ 不参与最终决策（Table 1 用 $\Theta_S$），但第 8 章大部分检验只在 θ⁰ 下做，摘要和结论里有几句 θ⁰ 下的结果被写成了一般结论。已在 $\Theta_S$ 下重跑这些检验，Seattle 全部保持第一 | 否，但有两句结论措辞需改 |
| 9 | 权重是否合理 | **结构合理，但 $\Theta_S$ 实际压低了安全的权重**：平均只有 0.127，低于平均份额 1/7。若规定"安全 ≥ 1/7"，Seattle 仍第一（68.3%），**Denver 从第二掉到第四**。需要团队决定 | 若采纳"安全 ≥ 1/7"，会改变第 2–4 名 |
| 10 | 付费许可/不能再分发不应作为不选的理由 | **同意**。两处都有更实质的理由，可以替换 | 否 |

需要团队拍板的有三件事：第 4 项（交通死亡底线去不去）、第 9 项（加不加"安全 ≥ 1/7"），以及之前遗留的 Chicago 犯罪口径（见第 8 项末尾的新数字）。

---

## 1. 可负担性和包容性"刻意分开"

**原文位置**
- 摘要页："Affordability and inclusion are deliberately kept apart."
- 3.1 节："In particular, affordability (can the family pay?) and inclusion (is the student treated fairly?) are different questions and are never merged."

**来源。** 这是你在 U20261111 的建模要求（"可负担性和包容完全是两个高度独立的点，不宜合并"），AI 把它当成了论文卖点写进去。七个领域本来就各自独立，单独强调这两个，读者会以为其他领域可以合并，或者以为曾经有人把它们合并过。

**改法。** 两句都删掉。3.1 节保留前一句"Each domain answers one question, and the domains stay separate even when their measures are correlated."，已经够用。

---

## 2. "cannot rely on a car"意义不明

**原文位置。** 标题、摘要定义、1.1、1.2 定义、假设 1、P3 理由、9.1 画像表、结论第 1 条、新闻稿导语，共 9 处。

**问题。**
1. 论文从没说清楚这是什么意思：是家里没车？学生不会开车？还是家长没空每天接送？
2. 9.1 节有一个"Student without a car"画像。主模型已经假设学生不能依赖汽车，那这个画像和主模型有什么区别？读者会直接卡在这里。
3. 这个前提很重要：P2、P3 两条偏好陈述和整个出行领域都以它为理由，不能删，只能讲清楚。

**数据支持（新算，NHTS 2022 全国样本，加权点估计）**

| 指标 | 数值 |
|---|---|
| 14–18 岁出行中，坐别人开的私家车 | 49.8% |
| 自己开车 | 24.3% |
| 步行、自行车、公交等 | 26.0% |
| 14–15 岁有驾照（是驾驶者） | 3.4% |
| 16–17 岁 | 50.0% |
| 18 岁 | 78.2% |

也就是说，高中生一半的出行要靠别人开车。我们的模型问的是：如果没有人能每天接送，这个城市还剩下多少机会。

**改法**

(a) 1.2 节"Three features of this definition…"一段之后加一段：

```markdown
**"Cannot depend on car rides."** The student does not drive and has no adult who can drive her to school, practice or work every day, so daily trips are made on foot, by bike or by transit. This describes many teenagers: in the 2022 National Household Travel Survey, half of all trips by 14–18-year-olds were as a passenger in someone else's car, and only half of 16–17-year-olds were drivers [26]. A city that works for such a student also works for one who sometimes gets a ride.
```

参考文献加第 26 条：

```markdown
26. Federal Highway Administration. *2022 NextGen National Household Travel Survey, Core Data V2.1*. https://nhts.ornl.gov/
```

(b) 9.1 节画像改名，并说明和主模型的区别：

- 表格行 `| Student without a car |` 改为 `| Fully transit-dependent student |`
- 表格前加一句：`The main model assumes the student cannot count on daily rides; the transit-dependent profile assumes no rides at all, so it adds a floor on transit coverage.`
- 图 6 的标签来自 `run_extensions.py` 的 `PROFILES`，改名后需要重跑 `run_extensions.py` 和 `make_figures.py`。

(c) 标题可以保留。如果嫌范围太窄，可以改为 "Floors First, Then Freedom: Ranking 25 U.S. Cities for High Schoolers"，把"不能依赖汽车"留给定义部分说明。这是风格选择，不影响内容。

---

## 3. 1.2 节"低租金买不回危险街道"

**原文。** `**Floors** come before trade-offs: a low rent should not buy back a dangerous street.`

**问题。** 你说得对：现实中很多家庭正是用安全换房租，这个例子等于在说他们做错了，读者会不同意。而且房租本身也是底线之一，用它举例反而混淆了"底线"和"权衡"。

**改法**（用论文实际使用的指标）：

```markdown
**Floors** come before trade-offs: no number of after-school programs should make up for a violent-crime rate above 1,200 per 100,000.
```

注意：这条例子用的是暴力犯罪底线，而第 4 项发现这条底线的理由偏弱。如果团队按第 4 项的建议补上理由（"约为全国水平的 3 倍"），这个例子就站得住。

---

## 4. 四条底线是否合理

底线的含义是"超过这条线，其他方面再好也不能补偿"。所以每条底线都要回答两个问题：这真的是不能补偿的需求吗？线划在哪里有没有依据？

| 底线 | 线 | 外部依据 | 25 城中最接近的 | 是否实际起作用 | 评价 |
|---|---|---|---|---|---|
| 房租 ≤ 收入 50% | 50% | HUD"严重负担"标准 | San Francisco 50.4%（不通过）、San Jose 47.0% | **是**：San Francisco 不通过；收入扫描里会改变合格城市 | **合理**。有官方标准，而且住不起确实是硬约束 |
| 暴力犯罪 ≤ 1,200/10 万 | 1,200 | 论文只说"等于最差节点"，属于循环论证。全国 2023 年为 363.8，1,200 约为其 **3.3 倍** | Nashville 1,160（待定）、Houston 1,061 | 点估计下没有城市超线；只让 Nashville 成为"待定" | **勉强**。需要外部依据，可以写"约为全国水平的 3 倍"。另一个弱点是全市平均掩盖了街区差异（9.3 节已承认城市平均的局限） |
| 交通死亡 ≤ 20/10 万 | 20 | 同样只说"等于最差节点"。全国 2023 年为 12.21，20 约为其 1.6 倍 | Phoenix 18.3、Dallas 17.0 | **从未起作用**：90% 区间下 25 城全部通过 | **不合理**。见下 |
| 空气差的天数 ≤ 30% | 30% | AQI > 100 是 EPA 的"对敏感人群不健康"等级（哮喘学生受影响）；30% 这个比例没有标准 | Los Angeles 27.9%、Phoenix 27.4%（都待定） | 让两城成为待定；改用都市区监测站时 **Phoenix 不通过**（8.3 节没提） | **基本合理**，但阈值要给理由，并补上"都市区口径下 Phoenix 不通过" |

**交通死亡为什么不适合做底线**
1. **它不是"不能补偿"的需求。** 25 城中最高和最低相差约每 10 万人 15 例，一年的个人风险差约 0.015%。这类风险适合放在加权的安全领域里（它本来就在），不适合做一票否决。
2. **指标和人群不匹配。** 这是全年龄、按事故地点统计的数据，包括高速公路上的司机和过路人。对不开车的高中生，更相关的是行人和骑车者的死亡数据。FARS 有这两项：25 城中位数 3.57/10 万，与全部交通死亡的 Spearman 相关系数 0.87。
3. **它从没生效。** 删掉它，任何城市的通过/待定/不通过状态都不变。

**改法（二选一，需团队决定）**
- **A（推荐）：去掉交通死亡底线**，只保留为安全领域的加权指标。代码改 `core.py` 的 `FLOORS`，重跑后所有结果数字不变（因为它从未生效），论文改 5.2、6.2、新闻稿里"四条底线"的说法为"三条"。
- **B：保留但补上理由。** 5.2 节替换如下：

```markdown
The rent floor is HUD's "severe burden" line [12]. The violent-crime floor is about three times the 2023 national rate of 363.8 per 100,000 [5]; the traffic floor is about 1.6 times the national rate of 12.2 [6]; the air floor means that air is unhealthy for students with asthma on nearly one day in three. No city's multi-year average crosses the last three floors, and three cities come within measurement error.
```

无论选 A 还是 B，8.3 节 "Metro-area air monitors put Seattle first" 后面都应补：`; under metro monitors Phoenix fails the air floor`。

---

## 5. 3.2 节"大学排名"的理由

**原文。** `| College and university rankings | Measures adult institutions; what reaches a student is captured by dual-enrollment courses |`

**你的建议**：正确的理由应该是"一个地区有好大学，不代表本地高中生能上好大学"，前提是先确认大学不会系统性偏向本地学生。

**核实结果。** 这个前提**部分不成立**：公立大学确实偏向本地学生，但偏向的单位是"州"和"每所高中"，不是城市。
- **UT Austin**：自动录取 Texas **每一所**高中排名前 6% 的学生，州法律规定自动录取要占本州新生名额的 75%（[UT News](https://news.utexas.edu/2017/09/15/growth-in-texas-drives-automatic-admission-to-top-6-percent)；[TEA](https://tea.texas.gov/about-tea/news-and-multimedia/correspondence/taa-letters/the-university-of-texas-at-austin-automatic-admission-policy-1)）。
- **UC**：Eligibility in the Local Context 保证**每所**加州高中前 9% 的学生能被某个 UC 校区录取（[UC Admissions](https://admission.universityofcalifornia.edu/admission-requirements/first-year-requirements/california-residents/local-guarantee-elc.html)）。
- 州内学费也是按州居民身份给的。

所以，住在 Austin 的高中生并不比住在 El Paso 的更容易进 UT Austin；住在 San Jose 的也不比住在 Los Angeles 的更容易进 UC。我们的 25 城里有 6 个在 Texas、4 个在 California，按城市给"附近大学"打分会在同一个州内制造虚假差异。私立大学面向全国招生，也没有按城市给的优惠。

唯一真实的"附近"好处是读大学时可以住家里、省住宿费，但那是高中毕业以后的事，不在我们的定义之内。

**改法**

```markdown
| College and university rankings | A nearby top university does not make it easier for local students to get in. Public universities favor residents of the state and the top students of every high school in it (UT Austin admits the top 6% of each Texas high school; UC guarantees a place to the top 9% of each California high school), so every city in a state gets the same advantage; private universities admit nationally. What a city adds before graduation, college courses taken in high school, is measured by dual enrollment |
```

这一格偏长。如果版面紧，可以把例子挪到表格下面作为脚注。

---

## 6. 3.3 节 "consolidated 'balance'"

**原文。** `using the Census definition of each city (for Indianapolis and Nashville, the consolidated "balance")`

**含义（已在 Census 数据中核实）。** Indianapolis 和 Nashville 都是市县合并的城市。合并后的辖区里，还有一些保留自己政府的小镇。Census 的"balance"指合并辖区扣掉这些小镇之后剩下的部分，Census 的城市人口排名用的就是这个数（[Census 定义](https://www.census.gov/programs-surveys/popest/guidance-geographies/terms-and-definitions.html)）。我们的人口文件 `sub-est2025.csv` 显示：

| 城市 | 合并辖区人口 | balance 人口 | 被扣掉的小镇（例） |
|---|---|---|---|
| Indianapolis | 910,638 | 901,116 | Clermont、Homecroft、Meridian Hills、Rocky Ripple 等 |
| Nashville | 745,904 | 721,074 | Belle Meade、Berry Hill、Forest Hills、Oak Hill、Goodlettsville（部分） |

（Indianapolis 所在县里的 Beech Grove、Lawrence、Southport、Speedway 本来就不属于合并辖区。）

**口径是否一致。** 一致。城市边界（SLD 街区组选取）用的是同一个 balance 的 Census 地理编码（1836003、4752006），人口分母也是 balance。唯一例外是 Nashville 的犯罪率用 Metro Nashville 警局的辖区人口，这一点 4.1 节已经写明。

**改法**

```markdown
The pool is the 25 most populous cities in the Census Vintage 2025 estimates [1], with each city as the Census defines it. Indianapolis and Nashville share their governments with their counties; for them the Census ranks the "balance", the merged city-county minus the small towns inside it that keep their own governments (for example Belle Meade in Nashville), and we use the same area for every measure.
```

---

## 7. 5.4 节"安全 vs 活动"的例子

**原文。** `People disagree about how much safety is worth compared with, say, activities.`

**问题。** 多数人会认为安全比课外活动重要，这不是"有合理分歧"的例子。

**改法**（换成两组确实有分歧的选择）：

```markdown
People disagree about how much, say, advanced courses are worth compared with after-school activities, or lower prices compared with better transit.
```

**提醒。** 如果团队认为"安全显然更重要"，就应该在模型里体现出来，而不只是换个例子。目前 $\Theta_S$ 实际给安全的权重偏低，见第 9 项。

---

## 8. 参考向量 θ⁰ 用在哪里，说清楚了没有

**θ⁰ 的全部用途（逐处核对）**

| 用途 | 位置 | 是否影响最终结论 |
|---|---|---|
| 参考成绩单、图 1、Table 1 的"Ref."列 | 6.1 | 否，展示用 |
| 计算示例 | 5.8 | 否 |
| 缺失值名次范围 | 4.3 | 否 |
| ELECTRE 参考版（内核只有 Chicago） | 6.4、8.2 | 对照方法 |
| 删一城的逆转检验 | 8.1 | 否（Table 1 版本也做了，同样 0 对） |
| 七种聚合规则对比 | 8.2 | **只在 θ⁰ 下做** |
| 单领域权重扫描（图 4）、节点平移、误差放大、删一个指标、替代数据口径 | 8.3 | 大部分只在 θ⁰ 下做 |
| 外部检验的领域得分 | 8.4 | 否 |
| 画像的参考冠军、收入扫描、联合指标 | 9.1–9.3 | 部分只在 θ⁰ 下做 |
| P1–P4 在边界上 | 6.4 | 说明用 |

**结论。** θ⁰ 确实不参与最终决策，最终排名是 Table 1（$\Theta_S$ 下的平均名次）。但论文没有明说这一点，造成两个问题：
1. 第 8 章的稳健性检验大多在 θ⁰ 下做。在 θ⁰ 下 Denver 和 Seattle 只差 0.0005，所以这些检验证明的是"这三座城市领先"，不是"Seattle 第一"。
2. 摘要和结论里有两句把 θ⁰ 下的结果写成了一般结论：
   - 摘要："Chicago is the most stable city when no weak spot may be traded away."
   - 结论第 3 条："Chicago leads whenever no weakness may be traded away."

   在 $\Theta_S$ 下用低替代性的 CES（ρ = −1）重算，**Seattle 54.4%，Chicago 22.5%**，Chicago 并不领先。"whenever"说过头了。

**在 $\Theta_S$ 下重跑原来只在 θ⁰ 下做的检验**（10,000 组，带数据噪声，CES 两行用点估计数据）：

| 检验 | Seattle 第一 | 其他 |
|---|---|---|
| 基准（同 Table 1，另一组数据噪声） | 64.2% | Denver 23.2% |
| 数据误差 ×2 | 51.5% | Denver 25.6% |
| 数据误差 ×4 | 33.7%（平均名次仍最好） | Denver 24.2%、New York 17.4% |
| 都市区空气数据 | 73.7% | Denver 15.1% |
| 青少年交通死亡（泊松–伽马） | 72.2% | Denver 16.9% |
| 加权 CES，ρ = 0 | 66.2% | Denver 21.4% |
| 加权 CES，ρ = −1 | 54.4% | Chicago 22.5%、Denver 22.2% |
| Chicago 犯罪改为约 960/10 万（遗留问题） | 67.5% | **Chicago 降到平均名次 6.06、第一 0.0%** |

Seattle 在每一项里都保持第一。最后一行与遗留的 Chicago 问题有关：如果改用约 960 的口径，Table 1 里 Chicago 会从第 4 名降到第 6 名左右。

**改法**

(a) 5.4 节 θ⁰ 段落末尾加：

```markdown
$\theta^0$ is a benchmark, not our decision rule. It gives one transparent scorecard (Figure 1, Section 5.8) and the starting point of single-vector checks; the ranking itself is decided over $\Theta_S$ (Table 1).
```

(b) 8.3 节末尾加：

```markdown
- **The same checks under $\Theta_S$** (10,000 draws). Seattle stays first with data errors doubled (51.5%) or quadrupled (33.7%, still the best mean rank), with metro air monitors (73.7%), with the teen traffic estimate (72.2%), and under CES across domains at $\rho=0$ (66.2%) and $\rho=-1$ (54.4%, Chicago 22.5%).
```

(c) 摘要句改为：`Chicago leads at equal weights when no weak spot may be traded away.`；结论第 3 条的 "Chicago leads whenever no weakness may be traded away" 改为 `Chicago leads at equal weights when no weakness may be traded away`。

---

## 9. 权重是否合理

**合理的部分**
- 不给单一权重，只给允许范围（每个领域在平均份额的一半到两倍之间），再用线性规划和 SMAA 检查结论在整个范围内是否成立。这是这类问题的标准做法，比 AHP 打分更不容易被质疑为主观。
- 边际递减、最后一段至少 10%、领域内每个指标不被忽略，都有明确理由。
- 图 5 已经展示了范围收窄时结论怎么变。

**问题：$\Theta_S$ 实际压低了安全的权重**

$\Theta_S$ 下各领域的平均权重：

| 教育 | 出行 | 安全 | 健康 | 活动 | 包容 | 可负担 |
|---|---|---|---|---|---|---|
| 0.192 | 0.193 | **0.127** | 0.127 | 0.127 | 0.127 | 0.108 |

- 安全有 **69.5%** 的抽样低于平均份额 1/7，在 18.9% 的抽样里是七个领域中最低的。
- 原因是 P1–P4 把教育和出行抬高了，总权重固定为 1，其他领域（包括安全）就被一起压低。
- 论文的辩护是"严重风险由底线处理"。但第 4 项发现，暴力犯罪和交通死亡两条底线在点估计下从未生效，所以实际上安全既没有底线保护，权重也偏低。评委很可能会抓住这一点。

**加一条安全陈述会怎样**（10,000 组，带数据噪声）

| 设定 | 安全平均权重 | 第一名比例 | 平均名次前四 |
|---|---|---|---|
| 现在的 $\Theta_S$ | 0.127 | Seattle 64.2%、Denver 23.2% | Seattle、Denver、New York、Chicago |
| $\Theta_S$ + 安全 ≥ 1/7 | 0.184 | Seattle 68.3%、New York 11.9%、Chicago 11.2%、**Denver 6.3%** | Seattle、New York、Chicago、**Denver（4.07）** |
| $\Theta_S$ + 安全 ≥ 其他每个领域 | 0.222 | Seattle 61.3%、Chicago 18.3%、New York 14.4%、Denver 2.7% | Seattle、New York、Chicago、Denver（5.05） |

**结论。** Seattle 第一不受影响。但 Denver 的第二名依赖"安全权重偏低"：Denver 的暴力犯罪率（978/10 万）是前四名里最高的。

**改法（需团队决定）**
- **A：采纳 P6"安全 ≥ 1/7"**，理由对应定义里的 "serious risk"。这样要重跑并重写 Table 1、6.4、摘要、新闻稿，第 2–4 名会变成 New York、Chicago、Denver。
- **B：保持 $\Theta_S$，但在 6.4 节补一段说明和敏感性结果**（推荐至少做这一步）：

```markdown
**Safety weight.** Because P1–P4 raise education and mobility, $\Theta_S$ gives safety 0.127 on average, below an equal share. Requiring safety to receive at least 1/7 keeps Seattle first (68.3% of draws) but moves New York and Chicago ahead of Denver (6.3%), whose violent-crime rate is the highest of the four leaders.
```

---

## 10. 付费许可、不能再分发不应作为不选的理由

**原文**
- `| Test scores (grades 3–8, SEDA) | Wrong age range; license does not allow redistribution |`
- `| Walk Score, AllTransit | Paid licenses; replaced by open EPA measures |`

**问题。** 你说得对：这两条都是"我们拿不到"，不是"不该用"。评委会认为这是在回避。而且两处都有更实质的理由。

**改法**

```markdown
| Test scores (SEDA) | Cover grades 3–8, not high school; state high-school tests differ by state and cannot be compared across our cities |
| Walk Score, AllTransit | Measure the same things as our EPA walkability and transit-access measures; scoring both would count the same thing twice |
```

---

## 试排

把本清单 1–10 的替换（交通底线按方案 B、安全权重按方案 B）与 `model_detail_audit_zh.md` 的全部替换一起套进论文副本试排：

- 正文 **25 页**，正好等于上限，另加 1 页 AI 报告。
- 摘要仍为 1 页，新闻稿仍为 2 页（第 23–24 页）。
- MathJax 无报错；第 6 页（3.2 节表格、3.3 节）逐行看过渲染图。

篇幅已经没有余量。如果交通底线改用方案 A（删除），或者把第 5 项大学一格的例子挪到脚注，可以省出几行。另外第 12、13、19、22 页因图表换页留有大块空白，调整图片位置或宽度也能省出空间。目录页的页码是手写的，正式应用时要按新版重新填写。

正式论文仍未修改。
