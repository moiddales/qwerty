# 模型写法细节评估：5.6 SMAA 及全文同类问题

日期：2026-11-12。对照对象：`paper/paper.md`（提交版），`analysis/model/` 下的全部模型代码，`himcm-modeling/` 里 92 篇 Outstanding 论文和写作指南。

## 结论

1. **5.6 节确实写得太简略。** 论文只用一段话概括了抽样过程，代码里实际有 4 层抽样、3 处拒绝规则、1 处排序处理、缺失值和零误差的处理、排名规则，以及 5 个输出量的计算方法。这些步骤论文都没有写。读者只看论文，无法复现 Table 1。
2. **全文还有 1 处同等严重的问题：5.7 节的 ELECTRE III。** 论文只写了三个阈值，没有给一致性、否决、可信度的公式，也没写蒸馏规则和抽样版用的是哪 400 组权重。另有 4 处中等问题、7 处小问题，见第三部分。
3. **按历年 O 奖论文的标准，这两节都需要补写。** O 奖论文写蒙特卡洛时，会用编号步骤或伪代码，并给出每个输出量的公式。2024A-14995 只把 MC-TOPSIS 当作对照模型，也写了 5 个小节和 7 个编号公式。项目里的写作指南（`himcm-modeling/guides/writing/structure-and-sections.md`）也要求："Algorithm: numbered steps, pseudocode or a flowchart for anything computational"。
4. **篇幅够用。** 提交版正文现在 22 页（AI 报告不计入），上限 25 页。我把第四部分 4.1–4.6 的替换文本套进论文副本试排了一次：正文变成 23 页，所有公式都能正常渲染，原论文没有改动。
5. **有一个数字需要更新。** 6.4 节写 Denver 的置信因子是 68.9%，这个数来自另一批抽样（种子 21），不是 Table 1 用的那批（种子 42）。用 Table 1 同一批抽样重算，结果是 66.7%；Seattle 两次都是 97.5%。补写 5.6 后，"中心权重取自 Table 1 的抽样"会写进论文，这个数字应改成 66.7%。

---

## 一、5.6 节：论文写了什么，代码实际做了什么

论文原文的意思是：从 $\Theta$ 或 $\Theta_S$ 里分三层均匀抽 10,000 组偏好，每组配一套加了 $N(0,s^2)$ 噪声的数据，缺失值从其他城市里抽，然后排名，报告三类结果。

代码（`core.py` 的 `Model.sample_theta`、`run_preferences.py` 的 `noisy_U`、`run_audit.py` 第 D 部分）实际做的事如下。

### 1. 最终权重怎么拼出来

每个 $\theta_{jl}$ 是三层份额的乘积：

$$\theta_{jl}=W_{d(j)}\times v_j\times g_{jl}$$

- $W_D$：领域 $D$ 的权重，7 个加起来等于 1；
- $v_j$：指标 $j$ 在本领域里占的份额，同一领域的加起来等于 1；
- $g_{jl}$：指标 $j$ 的价值在三段之间的分配，三段加起来等于 1。

论文只说"分三层"，没有写出这个乘积，所以读者不知道最后 60 个数是怎么拼成的。这正是你说的"怎么算最后的大权重"。

### 2. "均匀抽样"具体怎么做

每一层都用**平坦狄利克雷分布** Dirichlet(1, …, 1)。它在"所有非负、加起来等于 1 的向量"上是均匀分布。A-level 没学过的话，可以这样理解：把一根长度为 1 的棍子随机折成几段，每种折法的可能性一样。

### 3. 拒绝规则（论文完全没写）

| 层 | 抽法 | 保留条件（不满足就整组扔掉重抽） | 通过率 |
|---|---|---|---|
| 领域权重（7 个） | Dirichlet(1,…,1) | 每个 $W_D$ 都在 $[1/14,\ 2/7]$ | 1.17%（约 85 次留 1 次） |
| 领域内份额 | Dirichlet(1,…,1)，$n_D$ 维 | $\Theta$：每个 $v_j\ge 1/(3n_D)$；$\Theta_S$（P5）：$0.6/n_D\le v_j\le1.4/n_D$ | $\Theta_S$ 下：2 指标领域 40%，3 指标 11%，4 指标 3.2% |
| 三段份额 | Dirichlet(1,1,1)，**再从大到小排序** | 最小的一段 $g_{j2}\ge0.10$ | 49% |
| 整组（仅 $\Theta_S$） | 前三层拼好之后 | 满足 P1–P4 | 在已通过第一层的抽样中占 12.8% |

几点论文没交代的细节：

- **排序。** 边际递减（$\theta_{j0}\ge\theta_{j1}\ge\theta_{j2}$）不是靠拒绝实现的，是把抽到的三个数从大到小排好。因为平坦狄利克雷对三个分量是对称的，排序后在"有序区域"上仍然均匀。
- **为什么拒绝后仍然均匀。** 均匀分布截掉一部分以后，在剩下的区域上仍然均匀。所以"每层都均匀"这句话成立，但前提是写清楚"先在整个单纯形上均匀抽，再拒绝"。
- **每条约束都被精确执行。** 5.4 节的每一条约束都只限制某一层，拒绝规则和约束一一对应，所以 10,000 组全部落在 $\Theta$（或 $\Theta_S$）里。代码里有 `feasible()` 检查，抽查 2,000 组全部通过。
- **"逐层均匀"不等于"在整个 60 维集合上均匀"。** 这一点会影响读者如何理解"多常见"，论文应该说明，并给出理由：家庭真正有分歧的是领域权重，逐层均匀能让每种领域权重组合机会相等。
- **抽样分布不是 $\theta^0$ 的形状。** 抽出来的三段平均份额是 0.527 / 0.295 / 0.178，$\theta^0$ 是 0.563 / 0.289 / 0.148，说明 SMAA 的平均曲线比参考曲线更"直"。不需要写进论文，但答辩时可能被问到。

### 4. 数据怎么抽

- 每个数值独立加噪声：$\tilde x_{ij}=x_{ij}+s_{ij}\varepsilon_{ij}$，$\varepsilon_{ij}\sim N(0,1)$。论文没写"独立"这个假设。
- **20 个指标里有 7 个的 $s_{ij}=0$**：房租、价格平价、青少年票价、青少年工资、HRC 分数、步行指数、公交可达性。论文 4.2 节只提到"政策值（票价、工资、HRC）视为精确"，房租在 6.2 节提过，**步行指数、公交可达性和价格平价没有误差这件事全文没写。** 读者会以为数据噪声覆盖了全部 20 个指标。
- 缺失值：每次抽样都从报告了该指标的 24 个城市里**随机挑一个**，用它的值。论文写的是"drawn from the observed cities"，意思对，但没说是等概率挑一个城市。
- 加噪后可能超出节点范围（例如变成负数），不需要处理，因为 $\phi$ 会截断到 $[0,1]$。论文没说明这一点。
- 代码另外做过"同一城市同一领域的误差同向"的检验（`run_robustness.py` 第 5 部分，5,000 次）：Seattle 第一的比例从 64.8% 变成 60.7%，Denver 从 23.7% 变成 24.9%。**这个结果论文没报告**，加一句就能回应"误差独立"这个假设。

### 5. 怎么排名

每一轮算出 $U_i=\tilde\phi_i^{\top}\theta$，按从大到小排名：$r_i=1+\#\{k:U_k>U_i\}$。并列时代码按城市编号排，但实际没有出现并列（3,000 轮里最小分差为 $4\times10^{-8}$）。

### 6. 输出量怎么算（论文只列了名字）

| 输出 | 计算方法 | 论文写了吗 |
|---|---|---|
| 第一名比例 | 10,000 轮里 $r_i=1$ 的比例 | 只写了名字 |
| 前三比例 | $r_i\le3$ 的比例 | 只写了名字 |
| 平均名次 | 10,000 轮 $r_i$ 的平均值；**Table 1 按它排序** | 6.4 节提到排序，5.6 节没写公式 |
| 中心权重 | 城市 $i$ 拿第一的那些轮次里，$\theta$ 的平均值 | 只写了"central weight vector of winning draws" |
| 置信因子 | 把 $\theta$ 固定为中心权重，**另抽 5,000 套数据**，算城市 $i$ 拿第一的比例 | 没写 5,000 |
| 90% 名次区间（6.3 节） | $r_i$ 的第 5 和第 95 百分位数 | 没定义 |
| "只有数据噪声"（6.1、8.3 节） | $\theta$ 固定为 $\theta^0$，只抽数据 | 没定义 |

### 7. 精度

论文写了比例的标准误差 ≤ 0.005，但没写平均名次的标准误差。我重算的结果：平均名次的标准误差最大 0.03，Table 1 相邻两城的最小差距是 0.17（Austin 和 Boston、Houston 和 Jacksonville），所以 Table 1 的顺序不是抽样误差造成的。这个结论值得写进论文。

（复现说明：用 `run_preferences.py` 的种子 42 重跑，Table 1 的数字全部一致。）

---

## 二、历年范文怎么写这类过程

在 92 篇 O 奖论文里检索：

| 写法 | 论文数 | 例子 |
|---|---|---|
| 流程图 | 25 | 2020B-10876：蒙特卡洛求解流程图，配 4 个项目的小规模演示和收敛图（pp. 11–12） |
| 编号步骤（STEP 1/2/3） | 17 | 2024A-14995：MC-TOPSIS 写成 STEP 1–3 生成样本、STEP 1–4 计算、最后给出均值和标准差公式（式 27–33）。这是**对照模型**，也写了这么细 |
| 伪代码（Algorithm 1） | 8 | 2023A-13643：整个模拟循环写成伪代码（pp. 9–10）；2022A-12600：Algorithm 1 |
| 明确说明抽样分布 | 15 | 2023A-14076：写明每个随机量服从什么分布，重复 200,000 次 |

没有一篇用 SMAA 或狄利克雷抽样，所以找不到可以直接照搬的写法。但共同点很清楚：**蒙特卡洛的每一步抽什么、怎么抽、算什么，都用编号步骤或伪代码写出，输出量给出公式。** 我们的 5.6 节是整篇论文的核心结果（Table 1 的来源），目前的写法比这些论文的对照模型还简略。

项目写作指南里对应的两条要求：

- `guides/writing/structure-and-sections.md`："Algorithm: numbered steps, pseudocode or a flowchart for anything computational."
- `guides/writing/figures-tables-equations.md`："A reader should understand what the code does without reading it."

---

## 三、全文同类问题清单

按严重程度排序。"严重"指正文里的结果直接依赖它，而读者只看论文无法复现。

### 严重

| # | 位置 | 问题 |
|---|---|---|
| S1 | 5.6 SMAA | 见第一部分 |
| S2 | 5.7 ELECTRE III | 只写了阈值 0.05/0.20/0.80 和一句话解释。没写：(1) 每个指标的 0–1 分数是什么（代码用的是"该指标的分段价值 ÷ 该指标总权重"，即凹曲线归一化后的值）；(2) 指标权重 $W_j$ 怎么来；(3) 一致性 $c_j$、否决 $d_j$、可信度 $\sigma$ 的公式；(4) 蒸馏规则（区分阈值 $s(\lambda)=0.30-0.15\lambda$，资格分 = 胜过的城市数 − 被胜过的城市数）；(5) 两个顺序怎么取交集、内核怎么定义；(6) 抽样版用的是 Table 1 那批抽样的**前 400 组**，数据用点估计、不加噪声，而且每组权重同时改变 $W_j$ 和曲线形状。6.4 节和 8.2 节"Chicago 在内核里 50%"这类结论都依赖这些细节 |

### 中等

| # | 位置 | 问题 |
|---|---|---|
| M1 | 5.4 $\Theta$ | 四类约束只用文字描述。"最后一段至少 10%""不忽略指标""P5"没有公式。补一个集合式子，5.6 的抽样也会更好写（三层份额正好对应式子里的三类量） |
| M2 | 4.2 测量误差 | 7 个指标误差为 0，只交代了其中 4 个（3 个政策值和房租），步行指数、公交可达性、价格平价没提。误差独立的假设也没写 |
| M3 | 9.1 学生画像 | 论文说"把优先领域的权重加倍"。实际做法：以 2/7 为中心的狄利克雷分布（集中度 200）抽 5,000 组，再截断到 $\Theta$（不是 $\Theta_S$）。因为 2/7 正好是 $\Theta$ 的上限，抽出来的优先领域权重平均只有 0.26（是平均份额的 1.8 倍，不是 2 倍）。不满足画像底线的城市按点估计剔除，缺失值用中位数填补（主模型是随机抽取）。图 6 的数字依赖这些设定 |
| M4 | 6.4 置信因子 | 中心权重和 Table 1 不是同一批抽样，Denver 68.9% 应改为 66.7%（见"结论"第 5 条） |

### 小问题

| # | 位置 | 问题 |
|---|---|---|
| m1 | 5.5 | 可能赢家的线性规划只用文字描述，可以写成一行式子：$\max\varepsilon$ s.t. $(\phi_i-\phi_k)^\top\theta\ge\varepsilon\ \forall k\ne i,\ \theta\in\Theta$ |
| m2 | 5.2 / 6.2 | 联合通过概率怎么模拟（每次抽四个底线值，全部过线才算通过）没写；6.2 节用了 Bonferroni 下界，但全文没给定义 $1-\sum_k(1-p_k)$ |
| m3 | 5.3 | 括号里"lower is better 时不等式反向"是多余的：节点按从差到好排列，原公式对两种方向都成立，代码也只用了一个公式。建议改为"nodes are listed from worst to best, so the formula also covers lower-is-better measures" |
| m4 | 5.7 后悔值 | 公式写的是 $\max_{\theta\in\Theta}$，Table 1 的后悔值用的是 $\Theta_S$。应写"$\Theta$ (or $\Theta_S$)" |
| m5 | 6.1 / 6.3 | "data noise only"和"90% rank intervals"在 5.6 节没有定义（第四部分的替换文本已经包含定义） |
| m6 | 8.2 | CES、2-additive Choquet、熵权/CRITIC 只有结果表，没有公式。作为对照方法可以简写，但至少各给一行式子。代码实际用的是：领域分 ×7 归一化到 0–1，CES $=(\frac17\sum_D s_D^\rho)^{1/\rho}$；Choquet $=\bar s-\frac I2|s_M-s_A|$，$I=0.05/0.10$；熵权和 CRITIC 都先做 min-max 归一化 |
| m7 | 8.3 | 节点平移的具体做法（每个节点独立加 $U(-0.1,0.1)\times$ 节点跨度，再重新排序保持单调）没写；相关误差检验没报告（见第一部分第 4 小节） |

不需要改的部分：5.3 的分段公式、5.5 的两个线性规划和数据不确定性的推理、5.8 的算例、8.1 的留一城检验，这些写法已经能让读者复现。

---

## 四、可直接替换的英文文本

以下文本可以直接放进 `paper/paper.md`，数字都已核对。

### 4.1 替换 5.4 节"No measure ignored"之后、θ⁰ 段落之前（新增一段）

```markdown
In symbols, write $W_j=\sum_l\theta_{jl}$ for the total value of measure $j$ and $W_D=\sum_{j\in D}W_j$ for domain $D$, which has $n_D$ measures. Then

$$
\Theta=\Big\{\theta\ge0:\ \textstyle\sum\theta=1,\ \ \theta_{j0}\ge\theta_{j1}\ge\theta_{j2}\ge0.1\,W_j,\ \ \tfrac1{14}\le W_D\le\tfrac27,\ \ W_j\ge\dfrac{W_{d(j)}}{3\,n_{d(j)}}\Big\}.
$$
```

同时把表格里 P5 的说明改为：`${}0.6\,W_D/n_D\le W_j\le1.4\,W_D/n_D$`。

### 4.2 替换整个 5.6 节

```markdown
## 5.6 Step 5: how often each city wins (SMAA)

The LP says what is possible; SMAA [19] says how common it is. We repeat the following round $N=10{,}000$ times.

**(a) Draw a preference vector.** Every $\theta$ in $\Theta$ is a product of three nested shares,

$$
\theta_{jl}=W_{d(j)}\cdot v_j\cdot g_{jl},\qquad v_j=\frac{W_j}{W_{d(j)}},\qquad g_{jl}=\frac{\theta_{jl}}{W_j},
$$

and each constraint of Section 5.4 limits only one level. We draw each level from the flat Dirichlet distribution, which is uniform over all non-negative vectors that sum to 1, and redraw whenever that level breaks a constraint:

1. *Domain weights* $(W_1,\dots,W_7)$: kept only if every $W_D$ lies in $[\tfrac1{14},\tfrac27]$ (about 1 draw in 85).
2. *Measure shares* $v_j$ inside each domain: kept only if every $v_j\ge\tfrac1{3n_D}$; under $\Theta_S$, $\tfrac{0.6}{n_D}\le v_j\le\tfrac{1.4}{n_D}$ (P5).
3. *Segment shares* $(g_{j0},g_{j1},g_{j2})$ of each measure: sorted from largest to smallest (diminishing returns) and kept only if $g_{j2}\ge0.10$.
4. Under $\Theta_S$, the assembled $\theta$ is kept only if it also satisfies P1–P4.

All 10,000 vectors therefore lie in $\Theta$ (or $\Theta_S$). Sorting a flat Dirichlet draw keeps it uniform over the ordered region, so each level is uniform over its allowed range and every allowed set of domain weights is equally likely. The 60 values are uniform level by level, not over $\Theta$ as a whole; we chose this because families disagree mainly about domain weights.

**(b) Draw a data set.** Each value is perturbed independently, $\tilde x_{ij}=x_{ij}+s_{ij}\varepsilon_{ij}$ with $\varepsilon_{ij}\sim N(0,1)$; measures treated as exact (Section 4.2) have $s_{ij}=0$. A missing cell takes the value of a randomly chosen city among those that report the measure. A value pushed beyond the end nodes needs no correction, because $\phi$ clips it to $[0,1]$.

**(c) Score and rank.** $U_i=\tilde\phi_i^{\top}\theta$ and $r_i=1+\#\{k:\ U_k>U_i\}$. No two cities tied in any round.

**(d) Summarize.** Over the $N$ rounds,

$$
p^{(1)}_i=\frac1N\sum_{n=1}^{N}\mathbf 1\big[r^{(n)}_i=1\big],\qquad
p^{(3)}_i=\frac1N\sum_{n=1}^{N}\mathbf 1\big[r^{(n)}_i\le3\big],\qquad
\bar r_i=\frac1N\sum_{n=1}^{N}r^{(n)}_i .
$$

The final ranking (Table 1) orders cities by mean rank $\bar r_i$. A city's *central weight vector* $\theta^c_i$ is the average of $\theta^{(n)}$ over the rounds it wins; its *confidence factor* is the share of 5,000 new data sets in which it ranks first with $\theta$ fixed at $\theta^c_i$. The 90% rank interval runs from the 5th to the 95th percentile of $r^{(n)}_i$. Fixing $\theta=\theta^0$ and drawing only data gives the "data noise only" runs of Sections 6.1 and 8.3.

**Precision.** The standard error of a share is at most $\sqrt{0.25/N}=0.005$ and that of a mean rank at most 0.03, below one fifth of the smallest gap between neighbors in Table 1 (0.17).
```

替换后需要同步修改两处：6.4 节"Denver's is 68.9%"改为"66.7%"；5.1 记号表加一行 `$W_j$, $W_D$ | total value of measure $j$ and of domain $D$`。

### 4.3 替换 5.7 节 ELECTRE III 段落

```markdown
**ELECTRE III** [20] does not allow free trade-offs. It uses each measure's value on a 0–1 scale, $g_{ij}=\sum_l\theta_{jl}\phi_{ijl}/W_j$, and the measure weights $W_j$. For cities $a,b$ let $\delta_j=g_{bj}-g_{aj}$ be $b$'s lead on measure $j$. Then

$$
c_j=\operatorname{clip}\Big(\frac{p-\delta_j}{p-q}\Big),\qquad
d_j=\operatorname{clip}\Big(\frac{\delta_j-p}{v-p}\Big),\qquad
\sigma(a,b)=C\prod_{j:\,d_j>C}\frac{1-d_j}{1-C},\quad C=\sum_j W_j c_j ,
$$

where clip limits a number to $[0,1]$ and $(q,p,v)=(0.05,0.20,0.80)$. $c_j$ measures how much measure $j$ supports "$a$ is at least as good as $b$"; $d_j=1$ is a veto, a lead of at least 80% of the scale. $\sigma(a,b)$ is the credibility of that statement. At a cut level $\lambda$, $a$ outranks $b$ if $\sigma(a,b)>\lambda$ and $\sigma(a,b)-\sigma(b,a)>0.30-0.15\,\sigma(a,b)$; a city's qualification is the number of cities it outranks minus the number that outrank it. The descending distillation repeatedly removes the cities with the highest qualification, the ascending one those with the lowest. City $a$ is placed above $b$ if it is at least as good in both orders and better in one; the *kernel* is the set of cities with no city above them. The sampled version repeats this for the first 400 vectors of Step 5 under $\Theta_S$, with point data; each vector changes both the weights $W_j$ and the shape of each value curve.
```

同一节后悔值公式里的 `\max_{\theta\in\Theta}` 后面加一句："(over $\Theta_S$ in Table 1)"。

### 4.4 替换 4.2 节最后一句

原文：`Policy values (fares, wages, HRC points) are treated as exact.`

替换为：

```markdown
Seven measures are published standards or modeled values and are treated as exact: rent (HUD Fair Market Rents), price parity, youth fare, teen wage, HRC score, walkability and transit access. Errors are independent across cities and measures; Section 8.3 tests errors shared within a domain.
```

### 4.5 8.3 节"Data error"条目末尾加一句

```markdown
Letting all measures of a city's domain share one error, instead of independent errors, changes Seattle's share of first places under $\Theta_S$ from 64.8% to 60.7% (5,000 draws).
```

### 4.6 替换 9.1 节第一段

```markdown
The model answers different questions for different students by changing both their floors and their weights. The priority domain's weight is centered on 2/7, double the equal share, and the other six domains share the rest equally. We draw 5,000 vectors from a Dirichlet distribution centered on this profile (concentration 200) and keep those inside $\Theta$; because 2/7 is the upper limit of $\Theta$, the priority weight averages 0.26. Each vector is paired with a data set, and cities that fail the profile's floors are removed before ranking.
```

### 4.7 小问题的改法

- **m1（5.5）**：把"We test this by maximizing a margin ε…"改为式子 `$\max\varepsilon$ subject to $(\phi_i-\phi_k)^{\top}\theta\ge\varepsilon$ for all $k\ne i$, $\theta\in\Theta$`。
- **m2（5.2）**：在"20,000 simulated data sets"后加 "(the share in which all four values pass)"；在 6.2 节 Bonferroni 处加 "${}1-\sum_k(1-p_k)$"。
- **m3（5.3）**：括号改为 "(nodes run from worst to best, so the same formula covers lower-is-better measures)"。
- **m6（8.2）**：表格下加一行公式，内容见第三部分 m6。

---

## 五、建议的处理顺序

1. **必须做**：S1（5.6）、S2（ELECTRE）、M4（Denver 置信因子改为 66.7%）。这三项决定了核心结果能否复现，而且 M4 是一个与正文不一致的数字。
2. **应该做**：M1、M2、M3，以及 7 处小问题中的 m4、m5（成本低，m5 已经包含在 5.6 的替换文本里）。
3. **可选**：m1、m2、m3、m6、m7。
4. 改完后重新生成 PDF，确认正文不超过 25 页，再同步更新中文讲解版和组员 B/C/D 的讲解文档（5.4、5.6、5.7 都在里面）。

注意：Chicago 暴力犯罪数据是否改用约 960 的问题仍待决定。如果重算，第四部分里不依赖数值的文字不需要改，只需更新 4.5 的比例和 M4 的置信因子。
