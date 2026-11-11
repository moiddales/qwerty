# 模型计算结果（真实 25 城数据）

日期：2026-11-11（Asia/Shanghai）。状态：全部模型已搭建并在真实数据上计算，数值核验通过（见第 6 节），论文图已生成。最终模型为 **M2**；推荐在研究定义的偏好陈述下给出（第 4a 节）。

## 复现

依赖：Python 3.9+ 和 `analysis/model/requirements.txt` 中的包（`pip install -r projects/himcm2026A/analysis/model/requirements.txt`）。模型方法讲解（构造例子）见 [docs/model_guide/](docs/model_guide/README.md)。

```bash
python projects/himcm2026A/analysis/restore_city_archive.py --extract
python projects/himcm2026A/analysis/model/build_matrix.py
cd projects/himcm2026A/analysis/model
python run_model.py        # 约 25 秒
python run_extensions.py   # 约 20 秒
python run_preferences.py  # 约 1 分钟
python run_robustness.py   # 约 30 秒
python make_figures.py
python make_tables.py
```

| 文件 | 内容 |
|---|---|
| `analysis/model/build_matrix.py` | 从归档数据生成指标矩阵、测量标准差、口径说明和审计表 |
| `analysis/model/core.py` | 指标与固定参照节点（M0/M1/M2）、θ0、参数集合 Θ、线性规划、抽样 |
| `analysis/model/run_model.py` | 底线、参考榜、稳健偏好 LP、可能冠军、后悔值、SMAA、ELECTRE III、结构对照、敏感性、Poisson–Gamma、城内分布、外部对照 |
| `analysis/model/run_extensions.py` | 偏好信息曲线、单条偏好陈述、学生画像、GTFS 与 Chicago 口径对照、数值核验 |
| `analysis/model/run_preferences.py` | 研究定义偏好陈述下的稳健分析、SMAA、后悔值；抽样权重的 ELECTRE III |
| `analysis/model/run_robustness.py` | 数据区间下的精确稳健偏好、后悔值尺度、Poisson–Gamma 安全指标、下尾 α、误差相关、风险诊断、普查区联合可行性、空气质量地理口径 |
| `analysis/model/make_tables.py` | 模型阶段交付表：指标与补偿关系表、25 城总表、一城贯穿算例 |
| `analysis/model/make_figures.py` | 论文图 `results/figures/fig1—fig8` |
| `results/summary.json`、`extensions_summary.json`、`preferences_summary.json` | 全部关键数字 |

## 1. 指标与模型设定

七领域 20 项指标（M2），每项 4 个固定绝对节点、3 段分段线性，节点在计算排名前设定（`core.py` 中写明依据）：

| 领域 | 指标（M2） |
|---|---|
| 教育 | AP/IB/双学分选课人次每百生；非特许学校四年毕业率；每千生辅导员 |
| 安全 | 暴力犯罪率（2022—25）；交通死亡率（2021—24） |
| 健康 | AQI>100 天数比例；每千生校医/心理/社工；每 10 万未成年人青少年心理机构数 |
| 出行 | 45 分钟公交可达岗位数（SLD D5br）；步行指数；学生票价；周末/工作日服务比 |
| 课外 | 公园 10 分钟步行覆盖；青少年图书馆活动人次；校际运动参与；16—17 岁实际最低工资 |
| 可负担 | 两居室 FMR 占参考收入比例；非住房价格平价 |
| 包容 | HRC MEI 反歧视法与市政服务得分；校外停学率 |

- **θ0**：七领域各 1/7、领域内指标均分、段内按指数函数 k=2 分配（0.563/0.289/0.148）。这是中性参考假设，队内偏好判断确定后替换。
- **Θ**：凹性；每领域合计 1/14—2/7；领域内每项不低于均分的 1/3；末段不低于该指标的 10%。
- **底线**（参考需求，均做了扫描）：租金不超过收入的 50%（HUD 严重负担线）；暴力犯罪不超过 1,200/10 万；交通死亡不超过 20/10 万；AQI>100 天数不超过 30%。参考收入为 8 万美元。
- **缺失值**：参考榜用中位数并标出最差/最好填补下的名次；SMAA 从其他城市的观测值中抽取。缺失 3 格：San Francisco 校际运动（申报缺口）、San Diego SLD 频率（M2 不用该指标）、Washington MEI（未评级）。

## 2. 两次由真实数据推动的修订

| 修订 | 实际证据 | 修改 | 结果 |
|---|---|---|---|
| M0→M1 | San Diego 96% 人口街区组的 SLD 频率为缺码，而无站点比例只有 22%；San Francisco 一所成人特许学校占毕业队列 36%、毕业率 4%，Oklahoma City、Las Vegas 有同类情况 | 公交改用 NTD 人均服务小时并加周末保留率；毕业率只计非特许学校 | Kendall τ 0.893；San Francisco 13→8，Las Vegas 15→11，Philadelphia 10→15 |
| M1→M2 | PLAN 要求优先测量可达机会；服务小时与可达性 Spearman 0.895，两者同时计入会重复计量 | 用 45 分钟公交可达岗位数（GTFS 时刻网络计算）替换服务小时 | Kendall τ 0.967；冠军 Seattle→Denver（差 0.0005） |

对照表：`results/revision_M0_M1_M2.csv`；单独改毕业率、单独改公交的名次也列在其中。

## 3. 主要结果（M2）

| 项目 | 结果 |
|---|---|
| 参考榜前十 | Denver 0.8210、Seattle 0.8205、Chicago、New York、Boston、Austin、San Diego、San Francisco、Washington、San Jose |
| 底线 | San Francisco 未通过（租金占 8 万美元收入的 50.4%）；Los Angeles、Phoenix（空气）与 Nashville 待核；其余 21 城通过 |
| SMAA 广泛偏好第一名占比 | Denver 37.1%，Seattle 36.7%，Chicago 13.1%，New York 5.8%，Austin 3.9%（模拟标准误不超过 0.005） |
| 稳健偏好 | 在全 Θ 下 0 对必然关系、25 城都是可能冠军；最小最大后悔为 Seattle（0.302） |
| ELECTRE III（0.05/0.20/0.80） | 核心只有 Chicago；其后为 Denver、Seattle、Austin、San Diego、New York；与加性榜 Spearman 0.937 |
| 结构对照 | 指数 k=1/2/4 冠军均为 Denver；线性为 Seattle；CES 在 ρ<−0.85 时冠军为 Chicago；Choquet（出行×课外互补）为 Seattle；熵权为 New York |
| 固定尺度的性质 | 去掉任意一城，其余城市两两次序 0 次反转；熵权法 90 次反转 |

**结论**：Denver 与 Seattle 并列领先，Chicago 第三。

- 更看重**可负担性、健康和课外活动**的偏好下，Denver 领先。
- 更看重**安全、教育和包容**的偏好下，Seattle 领先。
- 强调**短板（低弥补，ρ<−0.85）或否决**的模型下，Chicago 领先。

Denver 与 Seattle 的领域分差（0—1 尺度）：

| 领域 | 教育 | 安全 | 健康 | 出行 | 课外 | 可负担 | 包容 |
|---|---|---|---|---|---|---|---|
| Denver−Seattle | −0.125 | −0.206 | +0.081 | −0.004 | +0.025 | +0.257 | −0.025 |

**单领域切换点**（其他领域按比例缩放）：

| 领域 | 切换 |
|---|---|
| 可负担 | 占比 ≥0.1425 时 Denver 领先，≥0.4175 时 Austin 领先 |
| 安全 | 占比 ≥0.145 时 Seattle 领先，≥0.2625 时 Chicago 领先 |
| 教育 | 占比 ≥0.1475 时 Seattle 领先 |

明细：`results/M2_champion_by_domain_share.csv`。

## 4. 偏好信息需要多少

| 偏好集合 | 必然成立的城市对（共 300 对） | 可能不被任何城市必然击败的城市 |
|---|---|---|
| 全 Θ（指标层面） | 0 | 25 |
| 领域 ±25%，领域内每项不低于均分的 60% | 7 | 20 |
| 领域 ±10%，领域内每项不低于均分的 85% | 56 | 15 |
| 领域内形状固定为 θ0，领域权重 1/14—2/7 | 95 | 8 |
| 领域内形状固定，领域权重 ±25% | 224 | 3 |
| 领域内形状固定，领域权重 ±10% | 276 | 2 |

不确定性主要来自领域内指标之间的分配，其次才是领域权重。“领域 A 不低于领域 B”这类单条排序陈述都不能确定前三名中任何一对的先后（`single_statements_deciding_top_pairs` 为空）。

## 4a. 研究定义下的偏好陈述（Θ_PLAN）

偏好陈述写在 `core.py` 的 `STATEMENTS_PLAN`，每条注明出处；用户 2026-11-11 确认采用，可直接修改或追加；也支持“城市 A 至少与 B 一样好”这类整体判断（`city_pref`）。当前五条：

| 编号 | 陈述 | 依据 |
|---|---|---|
| P1 | 教育权重 ≥ 可负担权重 | PLAN 3：预算决定资格（底线），达标后的经济余裕是软偏好 |
| P2 | 出行权重 ≥ 可负担权重 | 同上，针对不能依赖汽车接送的学生 |
| P3 | 出行权重 ≥ 1/7 | PLAN 4：研究对象不能日常依赖汽车接送 |
| P4 | 教育权重 ≥ 1/7 | PLAN 1/3：入学与课程机会是定义的第一项 |
| P5 | 领域内每项指标为均分的 0.6—1.4 倍 | PLAN 3：每项核心测量各自覆盖概念的一部分，不可忽略也不独占 |

θ0 满足全部陈述。结果（`results/M2_plan_preferences_*.csv`）：

| 项目 | 全 Θ | Θ_PLAN |
|---|---|---|
| 必然成立的城市对 | 0 | 4（Chicago、Denver ≻ Nashville；Austin ≻ Dallas、Fort Worth） |
| 可能冠军 | 25 | 19（排除 Philadelphia、Fort Worth、Phoenix、Dallas、Jacksonville、Nashville） |
| 最小最大后悔 | Seattle 0.302 | Seattle 0.154 |
| SMAA 第一名占比 | Denver 37%，Seattle 37% | Seattle 63.6%，Denver 23.5%，New York 6.0%，Chicago 5.8% |

逐条去掉检验：只有 P5 产生必然关系（去掉后回到 0 对、25 个可能冠军）。去掉任一条后 Seattle 仍是后悔最小、SMAA 第一。

**抽样权重的 ELECTRE III**（400 组参数，权重和价值形状同时抽样；`results/M2_electre_sampled_weights.csv`）：

| 城市 | 全 Θ 下进入核心的频率 | Θ_PLAN 下 |
|---|---|---|
| Chicago | 0.53 | 0.50 |
| Seattle | 0.31 | 0.41 |
| Denver | 0.34 | 0.24 |
| Austin | 0.21 | 0.09 |

**结论**：在 PLAN 的研究定义下，Seattle 是后悔最小、模拟中最常排第一的城市；Denver 在参考权重下与它并列。Chicago 在不可补偿（否决）结构下最稳。

## 4b. Θ_PLAN 下的其余稳健性（`results/robustness_summary.json`）

| 检验 | 结果 |
|---|---|
| 数据取 90% 区间的不利端（连续数据不确定，精确 LP） | 必然成立的城市对 0；Θ_PLAN 的 4 对都依赖点估计 |
| 效用平方后的最小最大后悔 | 仍为 Seattle；前三 Seattle、Denver、New York 不变 |
| 安全指标改用 Poisson–Gamma 收缩的 14—18 岁交通死亡率 | 冠军 Seattle；前五 Seattle、Denver、Chicago、New York、Boston；Kendall τ 0.947 |
| 下尾比例 α=0.1/0.2/0.3（公交可达性） | α=0.1 与 0.3 的 Spearman 0.885，单城最大相差 9 位 |
| 同领域误差完全相关与独立 | SMAA 第一名 Seattle 0.648 / 0.607，Denver 0.237 / 0.249 |

| 空气质量改用 CBSA 监测 | Spearman 0.916；参考冠军变为 Seattle；Phoenix 未通过空气底线 |

数据区间的求法：φ 对每项指标单调、θ≥0，所以对任意 θ，A−B 的最坏数据都是 A 取区间不利端、B 取有利端。因此“对所有 θ 和所有区间内数据都成立”可以用一个 LP 精确判定。

## 4c. 居住区层面的联合可行性（`results/joint_feasibility_tracts.csv`）

做法：ACS 2020—24 普查区租金中位数与贫困率（2020 普查区）经 2010—2020 对照表映射到 2010 普查区，再与 SLD 街区组可达性按普查区合并。各城有租金数据的人口覆盖率均 ≥98.3%。

| 城市 | 8 万美元可负担的居民比例 | 可负担且 45 分钟公交可达 6 万岗位 | 5 万美元：可负担且可达 |
|---|---|---|---|
| Philadelphia | 94.6% | 94.3% | 38.1% |
| Chicago | 87.5% | 86.1% | 36.5% |
| Denver | 68.2% | 68.1% | 6.6% |
| Seattle | 38.5% | 38.5% | 1.1% |
| San Francisco | 15.5% | 15.5% | 5.9% |

- **全市均值掩盖了联合不可行**：全市平均可达性与“可负担且可达”比例的 Spearman 只有 0.548。
- **替换后冠军不变**：用“可负担且可达”比例替换可达性指标后，冠军仍为 Denver，τ 0.953。
- **对中低收入家庭的含义**：Seattle 的高分主要属于能负担其中心城区的家庭。
- **高贫困普查区的可达性**：大多数城市高于全市均值；Washington（0.78）与 Dallas（0.79）低于均值。

## 5. 画像、公平与辅助模型

各画像的底线均为参考需求：

| 画像 | 合格城数 | 参考冠军 | SMAA 前三 |
|---|---|---|---|
| 参考家庭（8 万美元） | 24 | Denver | Seattle 0.41，Denver 0.40，Chicago 0.13 |
| 低预算家庭（5 万美元，可负担加倍） | 17 | Columbus | Chicago 0.37，Columbus 0.36，El Paso 0.13 |
| 无车学生（出行加倍；无公交可达人口不超过 25%） | 18 | Seattle | Seattle 0.45，Denver 0.41，Chicago 0.09 |
| 课外活动 | 24 | Denver | Denver 0.48，Seattle 0.41 |
| LGBTQ+ 学生（包容加倍；MEI 不低于 75） | 19 | Seattle | Seattle 0.51，Denver 0.36 |
| 需要心理健康服务（健康加倍；心理机构不少于 5/10 万） | 14 | Denver | Denver 0.59，Seattle 0.34 |
| 学业 | 24 | Seattle | Seattle 0.57，Denver 0.18，New York 0.11 |

- **城内分布**：公交可达性均值与下尾 20% 均值排名相差 ≥3 位的城市有 8 个（Chicago 2→5，El Paso 24→17，Jacksonville 25→20）。无公交可达人口比例最高的是 Oklahoma City 41.6%、Jacksonville 40.4%、Nashville 31.6%。San Francisco 只有 76.2% 的学生所在学校开设 AP/IB/双学分。见 `results/equity_within_city.csv`。
- **Poisson–Gamma**（14—18 岁交通死亡，2021—24）：合并率 5.96/10 万，χ²=116.4（df 24，p≈4e−14），a=5.85，b=98,062。收缩后与全年龄交通死亡率的 Spearman 为 0.752。
- **口径敏感性**：Chicago 暴力犯罪改用 CPD 2021 本地口径（960/10 万）后，Chicago 第 3→第 4，冠军不变。

## 6. 核验与外部对照

数值核验（`results/extensions_summary.json` → verification）全部通过：

- 3,000 个抽样参数 100% 在 Θ 内；
- 抽样分差全部落在 LP 上下界内；
- LP 后悔值不小于抽样后悔值；
- 冠军得分手算与矩阵计算一致；
- 领域贡献之和等于总分；
- θ0 在 Θ 内。

外部对照（不参与建模）：

| 对照 | Spearman | 方向 |
|---|---|---|
| YRBS 2023“因不安全不上学”与暴力犯罪（9 城） | −0.73 | 一致 |
| “未参加运动队”与校际运动参与（7 城） | −0.93 | 一致 |
| “悲伤绝望”与健康领域（11 城） | −0.76 | 一致 |
| “校内被欺凌”与包容领域（11 城） | +0.45 | 不一致：MEI 是市政政策，不反映校内体验 |
| GTFS 2026 周末比与 NTD 周末保留率（23 城） | 0.726 | 一致 |
| Opportunity Atlas 与总分（历史队列） | 0.32 | — |

## 6b. 模型阶段交付表（PLAN 第 9—10 节）

| 文件 | 内容 |
|---|---|
| `results/table_indicators_and_compensation.csv` | 20 项指标的定义与来源、方向、固定节点及依据、补偿角色（底线/可补偿/ELECTRE 否决）、参考权重、覆盖与取值范围 |
| `results/table_master_25_cities.csv` | 25 城底线状态、参考得分与名次、两种偏好集合下的 SMAA 与后悔值、可能冠军、ELECTRE 核心频率、居住区联合可行性、推荐状态 |
| `results/WORKED_EXAMPLE.md`、`worked_example_Seattle.csv` | Seattle 逐步通过底线、分段价值、对 Denver 的 LP 区间、SMAA、后悔值与 ELECTRE |

25 城推荐状态：

| 状态 | 城市 |
|---|---|
| 领先推荐 | Seattle |
| 部分偏好下并列领先 | Denver、Chicago |
| 前三竞争者 | New York |
| $80k 不推荐（底线） | San Francisco |
| 研究定义偏好下不可能第一 | Philadelphia、Fort Worth、Phoenix、Dallas、Jacksonville、Nashville |
| 其余 | 参与排名 |

## 6a. 图

`results/figures/`：

| 文件 | 内容 |
|---|---|
| fig1 | 参考榜与领域贡献、底线状态 |
| fig2 | SMAA 名次接受度 |
| fig3 | 单领域权重变化下的冠军 |
| fig4 | 偏好信息曲线 |
| fig5 | M0→M1→M2 名次变化 |
| fig6 | 学生画像 |
| fig7 | 收入情景下的合格城市 |
| fig8 | 公交可达性均值与下尾 |

配色为已校验的类别色板，按固定顺序使用。

## 7. 剩余限制

- **偏好陈述**：STATEMENTS_PLAN（P1—P5）经用户 2026-11-11 确认采用。需要修改时编辑 `core.py`，并重跑 `run_preferences.py`、`make_tables.py`、`make_figures.py`。
- **可达性用的是岗位数**：D5br 以 2017 年岗位为目的地、2020 年时刻计算，学校和活动地点的逐点可达性需要原始 GTFS 与设施坐标。
- **底线阈值是参考需求**：结论随阈值的变化见 `results/floors_scan.csv`。
