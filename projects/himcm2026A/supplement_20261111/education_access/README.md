# 招生资格与课程可选性：持续补采

本目录是教育补采的可复核批次，覆盖冻结的25个城市关联来源。**全25城居民招生网络和课程实际选修条件仍在采集。** 每条事实限定到命名学区、校区、项目或大学提供方；跨市学区、特许学校和同城其他学区必须分别核查。

最新数量以 `education_access_validation.json` 为准。2026-11-11本批检查点有74个官方来源目录、67份有效本机HTTP正文、164条接受的政策事实；450个城市×主题格中136格有局部证据、314格尚未核实。任何有证据的格仍表示局部覆盖。所有城市保留，不给缺失格填0，不计算城市排名。

## 数据文件

| 文件 | 内容 |
|---|---|
| `education_access_facts.csv` | 逐事实长表，包含原始城市代码、学区/提供方范围、项目、年级、学年、来源、短证据定位和访问时间 |
| `education_access_catalog.json` | 人工编码的来源和待核事实输入；未通过正文/锚点核验的候选不会进入facts表 |
| `education_access_sources.csv` | 官方来源、适用期、最终URL、HTTP状态、字节数、SHA256、许可与取得状态 |
| `education_access_http_log.jsonl` | 本机真实HTTPS GET尝试，保留失败和后续通道变化；UTC时间带偏移 |
| `education_access_fact_validation.csv` | 每条候选事实的有效文档、证据锚点和发布验收状态 |
| `education_access_coverage.csv` | 全25城×18类字段的证据数量、空缺码及每类下一步；学区和校区覆盖须继续扩展 |
| `education_access_dictionary.csv` | 字段及缺失码解释 |
| `education_access_lea_research_queue.csv` | 从既有CCD2024-25抽出的714个城市×LEA校址关联，作为继续核查清单 |
| `raw_local/` | 本机完整网页、PDF响应与提取文本；本目录`.gitignore`排除，未获得整页再分发许可 |

LEA研究队列来自市界内运营且开设9—12任一年级的学校位置，不是居民可入读学区全集，也不是招生边界。队列中每个LEA仍标为居民资格映射待核。居民可能符合市界外学校资格；存在市内学校也不能证明居民可入读。

## 当前证据与方法

招生规则分别记录居住条件、地址/边界分配、择校选择、申请日期和学校容量。AP、IB和双学分分别记录资格、费用、排课和课程容量；考试资格与课程入选资格分开。双学分课程里的大学资格、学区审批、课程先修、交通和时间条件必须联合使用。

政策事实保留为`value_text`，数值`value`为空；GPA或年龄阈值仍属于条件化规则，不能当作城市指标得分。校区课程开设和学校录取席位也不能替代实际课程座位。未取得的座位/名额/费用和未核条件保留`UNVERIFIED`。

日期选择依据实际访问正文。SAISD搜索缓存为2026-27，但本机实时页是2027-28，已按实时页编码。Philadelphia旧公告与当前页面出现不同截止日，保留更正提示。HISD实时日期表的2027-28开放日为12月8日，搜索缓存另一页为12月6日，采用日期表并保留冲突。页面没有学年时标为当前未注明年份，不把2026-27政策回填为2027-28。Undated Dallas Woodrow Wilson页使用旧学院名称，保留待核提示。

先用官方搜索定位，再由用户本机`curl.exe`取得正文；少量最初请求使用Python urllib，原始失败日志保留。Apptegy/Thrillshare的正文来自页面实际嵌入的`window.clientWorkStateTemp` JSON内容块。PDF由本机已安装的PyMuPDF提取，记录PDF页码；HSPVA第2页及Dallas当前图表第1页已渲染核对。Dallas旧图表URL实测404，当前官方Dual Credit页链接的Google Drive文件已成功取得；英语AP卡片与西语页的先修措辞差异保留于质量注。全文仅本机保存，发布自主撰写的短事实、来源和元数据。

本机San Diego Unified招生/部分课程域、Phoenix College、De Anza和Fort Worth choice子域有403响应，原因仍待核；HTTP200有效的SDCCD规则仅支持college-side条件。Fort Worth主域已取得当前choice规则，子域失败记录仍保留。不得由403推断收费、数据未发布或某环境必能访问。

## 继续采集的顺序

1. 依`education_access_coverage.csv`核实全25城招生空格，优先San Diego学区招生、El Paso边界/转学、Houston学年日期，以及各城尚未确认的居民资格。
2. 用714行LEA研究队列和官方学区边界/地址查询识别全部居民提供方；建立独立的居民地理映射后，逐一核查同城其他学区与charter政策。
3. 取得官方2026-27/2027-28校区课程目录及课程申请流程，补AP/IB先修、年级、费用和排课；双学分覆盖尚不等于AP/IB覆盖。
4. 查公开招生席位、课程section和等候规则；没有公布名额时继续保留未知，不用学校/课程存在推算座位。
5. 对查明的现有规则做有限人工语义核验。正文/锚点检查只验证证据定位；政策适用范围与学年由人工编码保留。

复现（仓库根目录）：

```text
python projects/himcm2026A/analysis/collect_education_access.py
python projects/himcm2026A/analysis/collect_education_access.py --fetch
```

第一条重新提取已有本地正文并校验、刷新所有表。第二条仅取得没有访问记录的新来源，最多4个并发GET，逐结果追加日志。已失败来源只有明确换通道/链接后才使用`--fetch --source SOURCE_KEY`；不自动重试。脚本使用Python标准库、本机curl，PDF提取另用已安装的PyMuPDF（`fitz`），不产生注册或申请。

新机器从Git只有短事实/目录/日志，`raw_local`需重取；指定`--fetch --source`按来源复核。重取的是当前网页，不能重现旧时点动态内容；保留原日志与原文件哈希可区分版本。
