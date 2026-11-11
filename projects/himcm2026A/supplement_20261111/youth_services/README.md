# 青少年活动条件与心理服务可用性补采

采集日：2026-11-11，Asia/Shanghai。对象为冻结的25城，每城一条活动样本、一条心理服务样本，共50条条件记录。采用政府/公立机构或服务提供方的官方页面、项目目录和手册。先读取项目采集计划、缺口、数据README及知识库`himcm-modeling/guides/modeling-workflow.md`的数据溯源规则。

本表交付的是**官方项目样本的资格、地点、价格/减免、时间和进入程序证据**，并记录取得的公开等待/容量资料。它不是全城项目普查、统一抽样调查、参与率或城市评分；25城有记录也不代表每城所有字段已经解决。医保资格、可预约性、可独立到达和实际治疗各自保留。

| 文件 | 用法 |
|---|---|
| `program_conditions.csv` | 主表，50条；保留Census city_id、官方balance名称、项目证据范围及时间 |
| `data_dictionary.csv` | 主表32个字段、单位和缺失值约定 |
| `program_facts*.json` | 按5城批次保存的人工核验输入；可追溯到`source_ids` |
| `sources*.json` | 精确URL、官方来源身份、正文校验锚点、发布限制 |
| `source_access_evidence.csv` / `access_evidence.json` | 用户本机Python GET的时间、状态、类型、字节、实际本地路径和解析结果；200且正文锚点命中才算本机有效取得 |
| `curl_access_evidence.csv/json` | 针对4个已观察到的Python TLS失败，用Windows原生curl另行取得的证据；原失败记录保留 |
| `web_channel_evidence.csv/json` | 5个本地未完整取得但已读到官方索引/正文的来源；记录通道、日期和结局，不虚构本机HTTP200 |
| `city_domain_coverage.csv` | 25城×2领域样本覆盖；数字是记录数量，绝非服务容量 |
| `field_coverage.csv` | 非空字段数量；非空文本可能写明待核，必须连同主表阅读 |
| `validation.json` | 数据键、来源关联、城市州代码及本机内容检验结果 |
| `raw_local/` | 取得的HTML/PDF、全文提取和核验图；由本目录`.gitignore`排除，不发布 |

仓库根目录重建：`python projects/himcm2026A/analysis/collect_youth_services.py --fetch`。程序保留已经记录的请求结果，仅抓新源；复算CSV用同一命令去掉`--fetch`。4个原生curl检查由`analysis/collect_youth_services_curl.py`单独执行，再运行主程序汇总。运行依赖本机现有requests、lxml及PyMuPDF。人工编码不由关键词自动推断；正文锚点只证明取得的内容正确，不能替代逐项核实。

## 字段含义

- `city_id`、`census_city_name`来自既有`data/metadata/cities.csv`；候选城市名称不改变县/机构服务范围。
- `age_min`/`age_max`只在官方明确数值时填写。年级、针对人群、临床条件及原文年龄冲突在`age_grade_rule`/`residence_eligibility`中说明。18岁覆盖与17岁截止严格区分。
- `fee_usd`只填明确适用的金额；`fee_unit`说明按年、周或次计费。0仅表示来源确证免费；未知留空。费用规则与减免、保险、自费条件单列。
- `schedule`分清项目时段、楼宇开放时间及办理时段；`registration_appointment`和`referral_rule`保存监护、材料、预约/转诊或面试条件。
- `capacity_number`搭配`capacity_unit`/`capacity_rule`。Dallas的25,000是2026年**最多发放通行证**，并非现有空位、总活动容量或实际参与者。
- `wait_days`目前仅Seattle有值：2026-11-01官方dashboard的Seattle/Magnuson Behavioral Health部门**新患者转诊创建至面对面预约的中位历日37天**。该数值经过本地PDF表格渲染核对；不是青少年专属/全城等待，也不是对新申请者的承诺。
- NYC“数日匹配”、Nashville“1–2个工作日回复”、DC“当日urgent assessment”、Boston药物评估按可用时段、Las Vegas于2024-10-15发布的“无等待名单”各保留原义。均未换算成未观测到的0天或确定等待。
- `observation_period`为项目/政策/统计的适用时间；HTTP `checked_at`是访问时间，两者不同。`quality_note`保存日期、范围、服务形式和已知冲突。

## 取得结局与待核字段

已检索并编码全25城官方样本，来源台账91项。Python GET有80项HTTP200且内容锚点命中；另4项以原生curl取得有效内容，合计84项本机有效取得。原始403、404及TLS/传输中断记录保留。余下7项中，5项官方索引/正文已通过网页检索通道核实，2项为已替换的旧目录链接。网页检索正文与本机下载成功分开记录。San Diego旧2025目录404后，已从实时官方HTML解析出September2026目录并取得有效PDF。Nashville旧summer链接404，当前fall PDF已取得并渲染核对，主表使用2026秋季时段。

当前缺口仍包括多数项目数值名额、实时空位、青少年专属治疗等待、逐项自费价、部分项目精确年龄/时段/地址，以及居住地点到服务点的联合可行性。机构数、服务人次、楼宇面积、电脑数、通常出席人数均未充当等待/容量。

Indianapolis活动使用2026-11-12图书馆活动，旧2025课程仅留访问台账；El Paso的2026文件名与内文2025日期冲突，LA活动flyer未标明适用期，主表保留相应待核。San José心理样本明确针对LGBTQIA+且限全范围县Medi-Cal；Phoenix心理样本为15–25岁精神病专科、地点在Avondale/Mesa，不能代表Phoenix全体14–18岁学生的普通门诊。

## 许可与发布

未确立各网页/PDF的整份再分发授权。仅发布独立编码的短事实、统计数值、精确URL及访问证据；原件、提取全文与渲染图保存在`raw_local/`并排除Git。公开浏览不等于整份转载许可，受限原件不上传。没有付费、外联、提交表单或真实预约。
