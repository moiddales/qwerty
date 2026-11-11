# 模型计算结果（首轮，未经复核）

日期：2026-11-11（Asia/Shanghai）。状态：核心模型已在真实 25 城数据上跑通一遍；**结果未做逐项核验和排错**，接手者先复核再引用。

## 复现

```bash
python projects/himcm2026A/analysis/restore_city_archive.py --extract
python projects/himcm2026A/analysis/model/build_matrix.py
cd projects/himcm2026A/analysis/model && python run_model.py
```

- `analysis/model/build_matrix.py`：从归档数据生成 25 城指标矩阵 `results/indicator_matrix.csv`、测量标准差 `indicator_sd.csv`、口径说明 `indicator_notes.csv`、三份审计表 `audit_*.csv`。
- `analysis/model/core.py`：指标、固定参照节点、参考参数 θ0、参数集合 Θ、线性规划和抽样。
- `analysis/model/run_model.py`：全部模型计算，输出 `results/*.csv` 与 `results/summary.json`。

## 模型设定

- 七领域 19 项指标（M0），每项 4 个固定节点、3 段分段线性；节点为预设绝对值，不随候选城市变化（见 `core.py` 的 `SPEC_M0`）。
- θ0：七领域各 1/7，领域内指标均分，段内按指数函数 k=2 分配（0.563/0.289/0.148）。这是中性参考假设，队内偏好判断到位后替换。
- Θ：凹性；每领域合计在 1/14—2/7；领域内每项指标不低于均分的 1/3；末段不低于该指标的 10%。
- 底线（参考需求，已做扫描）：两居室 HUD 租金不超过参考收入 8 万美元的 50%；暴力犯罪 ≤1200/10万；交通死亡 ≤20/10万；AQI>100 天数 ≤30%。
- 缺失值：参考榜取有数据城市的中位数并标记，另给最差/最好填补下的名次；SMAA 从其他城市的观测值中抽取。

## 真实数据审计发现 → 重大修订 M0 → M1

1. **SLD 公交频率缺码**：圣迭戈 96% 人口所在街区组 D4c 为 −99999，而 D4a（到站距离）缺失仅 22%，是频率数据缺失而非没有公交（`audit_sld_transit_coverage.csv`）。NTD 2022—2025 显示圣迭戈人均服务小时 1.11，高于中位数 0.85。
2. **毕业率被特殊学校拉低**：旧金山一所面向成人的特许学校占毕业队列 36%、毕业率 4%，把全市值拉到 56%；俄克拉荷马城一所特许学校占 51%（48%）；拉斯维加斯一所占 21%（7%）（`audit_graduation_outlier_schools.csv`）。
3. M1 改动：公交改用 NTD 主运营商固定线路人均服务小时，并加入周末服务保留率；毕业率只计非特许学校。M0 与 M1 的 Kendall τ = 0.893；旧金山 13→8，拉斯维加斯 15→11，费城 10→15。对照表 `revision_M0_vs_M1.csv`。

## 主要结果（M1）

| 项目 | 结果 |
|---|---|
| 参考榜前十 | Seattle、Denver、Chicago、New York、Boston、Austin、San Diego、San Francisco、Washington、San Jose |
| 第一、二名差距 | 0.0034（Seattle 0.8169，Denver 0.8135） |
| 必然偏好关系 | 300 对中 0 对；25 城全部是可能冠军；无帕累托被支配城市 |
| 最小最大后悔 | Seattle，0.302 |
| SMAA 广泛偏好第一名占比 | Seattle 35.2%，Denver 30.6%，Chicago 17.1%，New York 7.6%，Austin 4.9% |
| 底线 | San Francisco 未通过（租金占 8 万美元收入 50.4%）；Los Angeles、Phoenix、Nashville 待核 |
| Bonferroni 下界与联合模拟的最大差 | 0.0015 |
| ELECTRE III 平均位置前五 | Austin、Chicago、Denver、Seattle、Columbus；与加性榜 Spearman 0.852 |
| 结构对照 | 指数 k=1/2/4 冠军 Denver；CES ρ<−0.2 冠军 Chicago；熵权冠军 San Francisco |
| 节点 ±10% 扰动第一名占比 | Denver 48.8%，Seattle 36.6%，Chicago 14.4% |
| 逐项去掉一个指标后的冠军 | Seattle 10 次，Denver 6 次，Chicago 4 次 |
| 青少年交通死亡 Poisson–Gamma | χ²=116.4（df 24），存在过度离散；a=5.85，b=98062 |
| 外部对照 | Opportunity Atlas 与总分 Spearman 0.33；YRBS 上学不安全感与暴力犯罪 −0.73（9 城） |

结论：Seattle、Denver、Chicago 三城领先，三者之间的先后取决于偏好和价值函数形状，没有稳健冠军。

## 未运行

- 时变网络可达性（CSA）：原始 GTFS 和设施坐标不在仓库内。
- 校级 AP/IB 覆盖份额：读表出错，已从脚本移除。

## 接手后要做

1. 逐项复核 `build_matrix.py` 的口径和 `run_model.py` 的每个模块（尤其 ELECTRE 蒸馏、SMAA 画像情景、底线三态）。
2. Θ 目前太宽（0 对必然偏好）。补充队内偏好判断收紧 Θ，再重算稳健关系。
3. 按 `RISKS.md` 逐条更新状态；把本轮两项审计发现写入修订记录。
4. 按 MODEL_RESULTS 的表格出图，写论文与新闻文章。
