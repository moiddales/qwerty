# 数据来源目录与访问核查

核查日期：2026-11-11（Asia/Shanghai）。对应 [收集方案](DATA_COLLECTION_PLAN.md)。

**当前采集结果见 [DATA_COLLECTION_STATUS.md](DATA_COLLECTION_STATUS.md) 和 [逐来源状态](data/metadata/source_acquisition_status.csv)。下方各节为采集前入口核查记录，旧的“尚未下载/待解析”不代表当前状态。** 本轮已完成全25城实际提取，版本变化包括新取得CRDC2023—24、FBI现行月度数据、NTL公交调查镜像和全25城青年票价。具体缺口见 [DATA_GAPS.md](DATA_GAPS.md)。

## 1. 人口、地理与家庭条件

| ID / 层次 | 官方入口与已确认版本 | 拟取数据与地域 | 访问路线、限制及替代 |
| --- | --- | --- | --- |
| S01 / A | [Census 城市人口](https://www.census.gov/data/tables/time-series/demo/popest/2020s-total-cities-and-towns.html)：Vintage 2025，2020—2025 序列 | 城市池、总人口、官方名称和地理代码；incorporated place / MCD 区分 | 页面列出排名 XLSX 和全国 CSV。下载链接已解析；网页工具不支持该文件格式，尚未完整下载 |
| S02 / A+B | [ACS Summary File](https://www.census.gov/programs-surveys/acs/data/summary-file.html)；[2025 发布表](https://www.census.gov/programs-surveys/acs/news/data-releases/2025/release-schedule.html)；[2024 五年资料](https://www.census.gov/data/developers/data-sets/acs-5year.html) | 已发布 2025 一年、2020—2024 五年；人口年龄、在校、租金和负担、收入、无车、宽带、青年就业；place/tract/block group | 优先 Table-Based Summary File，含估计和 MOE。数据 API 现要求免费密钥；不能照旧假定无密钥可查询。2025 五年版尚未按已发布计入 |
| S03 / A+B | [TIGER/Line](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html) | 城市、县、社区、学区等边界；与数据期对应的地域版本和关联表 | 下载格式为 GIS 数据；具体州/版本在城市池冻结后选择。2020/2010 社区代码及边界转换要单列，不能仅取字符串前缀匹配城市 |
| S21 / A+B | [BEA RPP](https://www.bea.gov/data/prices-inflation/regional-price-parities-state-and-metro-area)：当前 2024 观测，2026-02-19 发布，下一次计划 2026-12-10 | 州/都市区地区物价平价及分项 | 页面提供 downloadable data；具体文件待解析。地区价格已含租金的部分要与住房指标去重；不当作城市精确成本 |
| S22 / A+B | [HUD FMR](https://www.huduser.gov/portal/datasets/fmr.html)：FY2027 已列；保留研究基准对应旧版 | 不同卧室数的 gross rent 标准，county/FMR area/ZIP 小区域租金 | XLSX/历史 CSV 直接文件优先；API 需账户和 token。FMR 是规定用途下的租金分位标准，不是全市住房成交均价；FY 与输入调查年分开 |

已观察的 S01 文件地址：

- [人口排名 XLSX](https://www2.census.gov/programs-surveys/popest/tables/2020-2025/cities/totals/SUB-IP-EST2025-ANNRNK.xlsx)
- [全国人口 CSV](https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/cities/totals/sub-est2025.csv)
- S02 [汇总文件目录](https://www2.census.gov/programs-surveys/acs/summary_file/)。目录存在不代表目录中每项都已发布；按发布说明和文件实测确认。
- [Census 2026 API 密钥说明](https://www.census.gov/library/video/2026/adrm/requesting-a-census-data-api-key.html)：数据查询需免费密钥；元数据与数据请求的要求应分别核对。

ACS 候选表先依据对应版本的 table shells/variables 确认内容：B01001 年龄、B14001 在校、B23001 年龄就业、B25064 租金、B25070 租金负担、B08201 车辆、B28002 网络订阅等是检索起点，不把这些表名当作未经核对的字段实现。金额、单位、分母与 MOE 一起取得；年龄组不吻合时不得伪造精确 14—18 岁数值。

## 2. 教育与包容

| ID / 层次 | 官方入口与已确认版本 | 拟取数据与地域 | 访问路线、限制及替代 |
| --- | --- | --- | --- |
| S04 / A+B | [NCES CCD 2023—24 v1a](https://nces.ed.gov/use-work/dataset/2023-24-common-core-data-ccd-universe-files-version-1a)；[学校数据入口](https://nces.ed.gov/ccd/pubschuniv.asp) | 公立学校/LEA、年级、学生构成、教师等；2024—25 已见 preliminary directory，不能与完整定稿版混同 | 全国 flat/SAS 等文件路线；本轮部分页面超时，文件取得未证实。学校地址城市与居民招生资格分开 |
| S05 / A+B | [CRDC 数据](https://ocrdata.ed.gov/data)；[2021—22 官方说明](https://www.ed.gov/laws-and-policy/civil-rights-laws/civil-rights-data-collection-crdc/civil-rights-data-collection-crdc-2021-22-school-year) | 课程、参与分组、学校支持、纪律和差异；学校/LEA；已确认公开版本 2021—22 | 下载页有 JS 界面，ZIP 实际取得待核。负码与抑制需代码本。公开数据镜像仅在版本、许可核实后替代，不预先认定需要付费 |
| S06 / A+B | [ED Data Express FAQ](https://eddataexpress.ed.gov/resources/ede-guides/faqs)；[EDFacts ACGR](https://www2.ed.gov/about/inits/ed/edfacts/data-files/index.html#acgr) | 四年毕业率、毕业队列、学生组；已核实 EDE 2021—22 SEA/LEA 资料，更新年份/学校级下载待核 | 优先导出 CSV 和 Data Notes。率与队列文件配对；S/区间抑制不填零。旧目录出现 403；可用 EDE/州官方批量表继续找 |
| S07 / B | [SEDA Trends](https://edopportunity.org/trends/data/downloads/)；[2025.2 永久记录](https://purl.stanford.edu/np279jm6134)；[Opportunity 下载](https://edopportunity.org/opportunity/data/downloads/) | 测试、增长与分组背景；2025.2 / 2009—2025 趋势和 Opportunity 6.0 属不同产品 | 主要测试年级 3—8，不能称高中成绩。下载文字与实际文件链接并非都可解析，部分文档 403；取得及再分发条款待核 |
| S11 / B | [CDC Profiles 数据](https://data.cdc.gov/d/yn8z-e2cm)；[2024 校长问卷](https://www.cdc.gov/school-health-profiles/questionnaires/pdf/2024/2024-Principal.pdf) | 已见 2022+2024 组合资料，州/参与 LEA；学校支持、反欺凌、相关社团/政策 | 公开 CSV 出口见下；本轮未下载。参与辖区不是全国每个城市；指标可能覆盖初中和高中，不能直接标作全城高中生体验 |
| S23 / A+B | [HRC MEI](https://www.hrc.org/resources/municipal-equality-index)；[2025 报告](https://reports.hrc.org/municipal-equality-index-2025)；[城市说明](https://www.hrc.org/resources/municipalities) | 2025 版约 506 城，市政保护与服务分项 | 公开网页/PDF；未确认官方批量 CSV，部分访问 403。DC 不在同一 MEI 城市评分范围，不以另一量表直接顶替；用适用官方政策分项核查。再分发许可待核 |

S11 已观察的 CSV 出口：[Profiles 2022/2024](https://data.cdc.gov/api/v3/views/yn8z-e2cm/export.csv?accessType=DOWNLOAD)。精确变量和辖区覆盖要以取得文件确认。

学校心理人员字段可同时涉及教育和健康；按其职责明确指标归属，同一个字段不重复加分。HRC、Profiles、CRDC 分别测量不同层面的制度和服务，不能拼接为未经定义的“包容总分”。

## 3. 安全、环境与健康

| ID / 层次 | 官方入口与已确认版本 | 拟取数据与地域 | 访问路线、限制及替代 |
| --- | --- | --- | --- |
| S08 / A+B | [FBI Crime Data Explorer](https://cde.ucr.cjis.gov/) | 暴力犯罪及分项、ORI、报告月份、覆盖人口；逐年/机构 | 本轮页面呈 Loading，最新完整 25 城年份未确认。先找现成年度/机构下载和官方城市年报；2021 转换及漏报另列；不能把全国估计当某城观测 |
| S09 / A+B，微观 C | [FARS 查询](https://www-fars.nhtsa.dot.gov/main/index.aspx)；[STSI](https://cdan.dot.gov/stsi/stsi.htm)；[Traffic Safety Facts](https://cdan.dot.gov/tsftables/tsfar.htm) | 已见 2024 在线统计；死亡、道路使用者、城市/县、年龄；2024 final/ARF 状态需文件内确认 | 先现成地区表；不够再用事故/人员文件。事故地不等于居住地；2022 电动自行车分类变更需核对，不能与早期机械拼接 |
| S10 / A+B | [EPA AirData 下载](https://aqs.epa.gov/aqsweb/airdata/download_files.html) | 2025 年度 AQI/监测浓度；county/CBSA/monitor；有效监测日数、污染物 | 公开批量 ZIP 无需 AQS API 密钥；本轮下载目录实际 HTTP 200。CBSA AQI 不等于 city proper；2026 部分年不入全年比较；同站不同标准/POC 不随意重复平均 |
| S12 / B | [CDC YRBS 数据](https://www.cdc.gov/yrbs/data/)；[现成结果](https://www.cdc.gov/yrbs/results/index.html)；[FAQ](https://www.cdc.gov/yrbs/faq/) | 2025 数据已于 2026-09-21 发布；优先比例/置信区间，9—12 年级、参与州和学区 | 免费公开；district 文件存在不代表 25 城均覆盖。先取现成统计，原始个体文件仅作必要补充；使用调查权重和抽样说明 |
| S13 / B | [HRSA 下载](https://data.hrsa.gov/data/download)；[SDMS 官方目录](https://catalog.data.gov/dataset/shortage-designation-management-system-sdms) | Mental Health HPSA 区域/人口/机构指定、服务短缺背景 | 动态快照，时间需实际下载确认。入口访问不稳、原因未明；官方目录已列公开 CSV。区域型、群体型、机构型指定不叠加为同一人数；不等于青少年等待时间 |
| S14 / A 候选+B | [SAMHSA 2025 Mental Health Directory](https://www.samhsa.gov/data/report/2025-national-directory-mental-health-treatment-facilit) | 2025 名录，基于 2024 N-SUMHSS；机构位置、服务、年龄资格候选字段 | 索引列 Excel，页面直接访问 403，文件 URL 尚待解析。机构接受年龄待代码本确认；名录有自愿填报/漏报，数量不等于容量或质量 |
| S15 / B 背景 | [CDC PLACES 2025 place release](https://data.cdc.gov/d/vgc8-iyc4)；[FAQ](https://www.cdc.gov/places/faqs/index.html) | 成人 ≥18 岁的小区域模型估计；大部分来自 2023 BRFSS，部分 2022；place 边界 | 公开 CSV。PA/KY 对应部分 2023 来源指标缺失，须核对或使用一致旧版；不能用成人估计填青少年心理健康缺口 |

本轮观察到的下载地址（未宣称已下载）：

- S10：[2025 CBSA AQI](https://aqs.epa.gov/aqsweb/airdata/annual_aqi_by_cbsa_2025.zip)、[2024 county AQI](https://aqs.epa.gov/aqsweb/airdata/annual_aqi_by_county_2024.zip)、[2025 monitor concentrations](https://aqs.epa.gov/aqsweb/airdata/annual_conc_by_monitor_2025.zip)。
- S12：[2025 district 原始数据](https://www.cdc.gov/yrbs/files/sadc_2025/sadc_2025_district.dat)，列为后备，先找现成统计与说明。
- S13：[Mental Health HPSA CSV](https://data.hrsa.gov/DataDownload/DD_Files/BCD_HPSA_FCT_DET_MH.csv)。
- S15：[PLACES CSV](https://data.cdc.gov/api/v3/views/vgc8-iyc4/export.csv?accessType=DOWNLOAD)、[字段元数据](https://data.cdc.gov/api/views/vgc8-iyc4/columns.json)。

## 4. 自主出行与课外机会

| ID / 层次 | 官方入口与已确认版本 | 拟取数据与地域 | 访问路线、限制及替代 |
| --- | --- | --- | --- |
| S16 / A+B | [EPA Smart Location Mapping](https://www.epa.gov/smartgrowth/smart-location-mapping)：SLD V3，2021 版 | 全国 block group 的现成步行环境、街网、公交/站点等指标；Walkability Index | 官方 CSV/ZIP 已观察。底层来源年份混合；公交字段依 GTFS 覆盖。作为出行环境代理，不能把就业可达性称为青少年课外可达性 |
| S17 / A+B | [FTA NTD](https://www.transit.dot.gov/ntd/ntd-data)；[2025 Service](https://data.transportation.gov/Public-Transit/2025-NTD-Annual-Data-Service/74ek-quhs) | 报告年 2025，页面更新 2026-10-14；服务里程/小时、客流，agency/mode | 官方 CSV 出口已观察、未下载；需机构服务范围匹配。机构全年总量不足以衡量放学后是否有车，成人与学生不分 |
| S18 / B+C | [BTS NTM](https://www.bts.gov/national-transit-map)；[GTFS catalog](https://ntmcatalog.bts.gov/)；[历史档案](https://rosap.ntl.bts.gov/view/dot/75925) | 现成站点/线路；必要时历史 GTFS，用于放学和周末出行 | 档案列约 1.18 GB ZIP，未下载；内部年份与 feed 内容待核。按 snapshot 日期判断覆盖；当前 feed 不代替研究年的时刻表；每项许可单独记录 |
| S19 / A+B，空间 C | [TPL 下载](https://www.tpl.org/park-data-downloads)：已列 2026 ParkScore 和 City Park Facts | 100 大城市，公园步行覆盖、设施类别、面积；ParkServe 为更细空间数据 | 现成城市表优先。免费查看/下载与再分发分开；ParkServe May 2024 条款限制复制转发等，见第 6 节。城市表具体许可需确认；可用公园局开放统计替代 |
| S20 / A+B | [IMLS PLS](https://www.imls.gov/research-evaluation/surveys/public-libraries-survey-pls)；[FY2024 代码本](https://www.imls.gov/sites/default/files/2026-06/PublicLibrariesSurvey_FiscalYear2024_DataDocumentationandUsersGuide.pdf) | FY2024；图书馆系统 AE / outlet；网点、青少年活动场次和人次候选字段 | 子代理读取到代码本，主入口与主代理部分访问 403；FY2024 CSV 实际 URL 未解析。YAPRO/YAATTEN 在系统层级，出席人次不是独立高中生人数；核对包括线上与年龄口径。州官方镜像可作备选 |
| S24 / 可选 | [Walk Score research](https://www.walkscore.com/professional/research.php)、[定价](https://www.walkscore.com/professional/pricing.php)、[条款](https://www.walkscore.com/professional/terms-of-use.php) | 现成 Walk/Transit/Bike 等评分；版本按实际数据包 | API 密钥/套餐或研究授权；未找到公开批量包。禁止未经许可的缓存/再分发等条件，不能因网页可查就批量复制；用 S16 替代主干 |
| S25 / 可选 | [CNT AllTransit 方法](https://alltransit.cnt.org/methods/)、[FAQ](https://alltransit.cnt.org/faq/) | 当前说明采用 2022 人口与 2024 公交；city/CBSA 现成连接性、频率、就业可达性 | 定制数据收费询价，原始库专有；未找到开放批量 URL，不能承诺免费归档。优先 S16/S17；就业目的地与青少年活动区别保留 |

已观察的下载链接：

- S16：[SLD CSV](https://edg.epa.gov/EPADataCommons/public/OA/EPA_SmartLocationDatabase_V3_Jan_2021_Final.csv)、[SLD ZIP](https://edg.epa.gov/EPADataCommons/public/OA/SLD/SmartLocationDatabaseV3.zip)、[Walkability ZIP](https://edg.epa.gov/EPADataCommons/public/OA/WalkabilityIndex.zip)。
- S17：[2025 NTD Service CSV](https://data.transportation.gov/api/v3/views/74ek-quhs/export.csv?accessType=DOWNLOAD)。
- S18：[NTM 历史 ZIP](https://rosap.ntl.bts.gov/view/dot/75925/dot_75925_DS1.zip)。
- S19：[2026 ParkScore PDF](https://parkserve.tpl.org/downloads/historic/2026_ParkScoreRank.pdf)、[2026 设施 XLSX](https://parkserve.tpl.org/downloads/cpf/Amenities_Facilities_WEB_DATA_TABLES_City_Park_Facts_2026.xlsx)、[ParkServe ZIP](https://parkserve.tpl.org/downloads/ParkServe_shapefiles_05152026.zip)。
- S20：FY2024 文件尚待定位；已观察 [FY2022 CSV ZIP](https://imls.gov/sites/default/files/2024-06/pls_fy2022_csv.zip) 可作备用入口，不能由此猜造 FY2024 地址。

## 5. 独立验证、偏好证据与特定服务

| ID / 层次 | 来源与范围 | 收集用途与状态 |
| --- | --- | --- |
| S26 / B | [Opportunity Insights 数据](https://opportunityinsights.org/data/)；[Opportunity Atlas replication](https://doi.org/10.7910/DVN/NKCQM1) | 页面列社区、县、通勤区等统计及 crosswalk；具体文件/许可待核。用成长地点与成年结果作历史外部检验，匹配出生队列和边界；不用于给当前指数调出“满意相关性” |
| S27 / B/C | [Dryad：Fare free transit for youth](https://datadryad.org/dataset/doi:10.5061/dryad.612jm64fn)，UC Davis 作者；[CSV 文件](https://datadryad.org/downloads/file_stream/4253552) | 2024 Santa Cruz County 调查，2025-08-25 发布；392 行、127 变量。数据页和 README 可读，CSV 子代理访问 403，原因待核。用于交通与活动关系和测量设计，不外推 25 城参与率；README 列公开使用条件，实际归档保留引用 |
| S28 / A 缺口+B/C | 各入选城市/学区/州的官方开放数据、预算年报、学校报告卡、招生规则、公交票价、公园图书馆与青少年项目统计、适用政策 | 城市池冻结后逐城补充，具体 URL 目前尚未建立。先找官方现成汇总和开放目录；只对没有统一统计的重要字段统一人工编码。无须为展示复杂模型逐个抓取所有设施 |
| S29 / 参数证据储备 | 已发表的青少年调查、出行与活动研究、服务标准及原始政策说明 | 用于说明指标需求、可达性时限、合理偏好/阈值情景。具体来源需逐条核验；目前没有验证到覆盖 25 城、同时给七领域权重的统一调查。不能把成年人调查或数据方差直接当高中生权重 |

来源范围的判断：一个公开项目能证明“数据存在”，不能自动证明“它给出了本题所需的每个城市/年龄/年份”。搜索不到某个变量也不能证明该统计从来不存在。S28—S29 必须按明确问题继续检索，再决定保留或放弃。

## 6. 访问测试与限制证据

下表均为 2026-11-11 的有限核查。网页检索工具和运行环境 HTTP 请求是不同通道；尚未在用户实体电脑测试任何来源。

| 项目 | 实际观察 | 当前可下的结论 | 实施时动作 |
| --- | --- | --- | --- |
| Census API 小查询 | 运行环境 GET `https://api.census.gov/data/2024/acs/acs5?get=NAME,B01003_001E&for=place:51000&in=state:36` 返回 HTTP 200，但正文是标题含 Missing Key 的 HTML | 官方 2026 说明确认数据 API 需免费密钥；属于访问条件，不是已下载 JSON 或已证明云端屏蔽 | 首选公开 Summary File；确需 API 再集中处理密钥 |
| 人口排名 XLSX / 全国 CSV | 官方链接分别被网页工具报 Unsupported content-type（工具错误 400） | 工具解析限制；来源文件下载能力仍需实际文件请求确认 | 用普通文件下载并核验内容，不能据此报告来源无数据 |
| 人口猜测路径 | 早期试探 `sub-est2025_all.csv` 得到 404；后从官方页面找到 `sub-est2025.csv` | 原猜测 URL 无效，不能判定全国数据不存在 | 只把官方已观察链接列为实际候选 |
| EPA AirData 目录 | 运行环境 GET 下载目录 HTTP 200，返回预期 HTML | 目录当前可访问；尚未证明各 ZIP 完整下载和解析成功 | 取得需要的年度汇总 ZIP，核对行数、地域和年份 |
| IMLS | 主入口/主代理文档读取出现 403；子代理曾读到官方 FY2024 文档 | 访问结果不一致；原因待核，不能断言实体电脑必可访问 | 官方下载链接、州镜像或浏览器；保留不同通道结果 |
| HRC / SAMHSA / SEDA 部分页 | 官方内容有索引，部分直接打开 403 | 特定通道受阻，原因尚未区分 | 尝试官方附件/档案与可读页面，不把 403 解释成收费证明 |
| FBI CDE / CRDC | Loading 或 JS 页面，没有取得所需数据文件 | 界面/下载流程尚未完成 | 官方批量入口、受支持浏览器与官方镜像；必要时本地数据替代 |
| Dryad CSV | 公开数据页可读，子代理点击 CSV 返回 403 | 文件取得待核，未确认注册条件或云 IP 阻断 | 普通文件请求/仓库下载机制；最终核对许可与实际内容 |
| HUD | 官方说明 API 需要账户和 access token，同时列公开 XLSX/CSV | API 有条件，数据可另走公开文件路线 | 不为使用 API 而不必要地注册 |
| Walk Score / AllTransit | 官方列 API/研究授权、询价和使用条件，未观察到公开批量文件 | 有注册/商业或许可条件；研究数据价格不能拿另一套餐价格代替 | 免费替代优先；若不可替代再汇总准确报价/授权需求 |
| TPL ParkServe | [May 2024 条款](https://parkserve.tpl.org/downloads/ParkServe_Terms_of_Use_May_2024.pdf)明确限制复制、修改、公开展示、转发，允许个人非商业下载一份 | 下载公开不等于可上传 GitHub；含第三方权益。城市汇总表是否有单独授权仍待核 | 不转存受限包；确认许可或采用市政开放数据。引用少量事实与重发整包分别判断 |
| GitHub 目标分支 | GitHub 连接器读取和 `git ls-remote` 均取得 `1f853cac1fdb9d1bc5925d8c9f38a174d01d77db` | 仓库分支可读；既有文本提交路线可用 | 按文件实际大小验证数据上传，不把读取成功当大文件推送成功 |

**目前没有来源已经被证实为“该云端工作空间被屏蔽，但用户实体电脑肯定可下载”。** 后续如取得两端测试证据，再升级分类。

“事实上无法获取”目前也不作全局宣判。已经明确的限制包括部分调查只覆盖参与辖区、统计年龄与目标年龄不一致、特定版本缺失或抑制；具体城市字段应逐项核对后登记。无法取得精确数据时，代理、情景区间与未解决缺口必须清楚区分。

## 7. 下一步核查优先级

用户确认方案后，优先解决：

1. 取得 S01，冻结前 25 城及代码；S02/S03 建立分母和地域底表。
2. S08 的完整报告覆盖、S05/S06 的高中资料、S20 FY2024 文件、S23 的可比分项和 DC 缺口。这些直接决定核心测量是否成立。
3. 完成 S10/S16/S17 等现成公开汇总，核对跨地域、不同年份及学生专属性。
4. 确认 S19 再分发与替代路线；取得 S11/S12 的参与辖区清单，保留城市覆盖缺口。
5. 收 B 层的相关多年和分组数据，再根据具体模型缺口决定 C 层细化；每个批次同步记录实际文件和推送状态。

资料取得和清洗后的覆盖结论将写入 DATA_COLLECTION_STATUS.md；本目录作为来源证据继续更新，不覆盖历史尝试记录。

## 本地补采A-011/A-012（2026-11-11）

- S28教育：164条命名学区/课程事实、74个官方来源目录，450个城市主题格中136有局部证据；学校校址关联LEA队列仅研究入口，非居民招生分母。
- S28活动/心理：25城各一个公共活动/服务样本，共50条；91源，84份本机内容确认，其余网页证据及已替换链接分别登记。Seattle37日为单一儿童医院服务部门快照，Dallas25000为年度pass数量，不外推全城等候/实时名额。
- S29工资：25城三年龄组条件表，85次本机访问、51份内容确认；原始网页和第三方PDF保留本地，发布短事实、源引用、口径和真实未决条件。
- S18时刻：35个operator/mode feed原件已本地保存，全部关键关联验收通过；时效、必要机构和可再分发条件单独审查。原ZIP本地保留，发布registry/HTTP/验证与源缺陷证据。MobilityData目录CC0仅覆盖目录元数据。
- 既有受阻来源本机实测包括Census Missing Key HTML、NTM导出空目录、运营商直链及镜像、CDC网页403而JSON200、NHTSA目录403而方法报告PDF200；不能合并成单一云端屏蔽判断。
