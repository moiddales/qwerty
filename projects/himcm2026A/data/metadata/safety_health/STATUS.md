# 安全、环境与健康采集状态

采集时间：2026-11-11 UTC。所有25城均保留。实际文件与逐次访问证据见 `file_inventory.csv`、`access_log.jsonl`；逐城逐源覆盖见 `city_source_coverage.csv`。

## 已实际保存

- 原始文件 273 个，共 340,431,603 字节；提取文件 50 个，共 48,967,099 字节。原始数包含数据、说明、前端入口证据，不能全部称为数据集。
- 统一长表 `data/extracted/safety_health/city_observations.csv`：12,726 行，25城；保存来源、观测期、实际地理、质量说明。空值不填0。
- FBI 2021—2025 Offenses Known ZIP与resource-pages ZIP、Table8、方法PDF已下载；官方当前agency注册表提供25城关联主要机构ORI。Table8按方法为12个月完整报告。FBI人口保留为该警务机构人口。
- 后续补缺另取得FBI现行monthly summarized API：25城关联ORI×5犯罪类×2021—2025，共125份JSON、7,500个月度记录；保存每月机构人口、参与人口、actual counts与2026-10-15刷新日期。年合计要求12个有数值且参与人口>0的月，四类犯罪与violent total逐城逐年核对。出版Table8与现行API分别保存，不能混用版本。
- FARS 2021—2024全国CSV ZIP已下载，各约33—35MB。现成Table124后端实际401/403，因此使用事故及人员表，按事故地提取25城。2024为ARF。死亡总数与人员表INJ_SEV=4计数逐城逐年一致；14—18岁为精确年龄筛选。纽约由五县合并，避免原始CITYNAME混杂；其余保留FARS城市代码，balance边界需后续核验。
- EPA 2021—2025 county和CBSA AQI共10 ZIP；2025全部监测站年度污染浓度ZIP及说明。County、CBSA、监测站均保留真实层级；每城多县单列，没有平均成城市值。
- YRBS官方YouthOnline API：参与地理、题目、年份、dashboard元数据及17个关联学区2021/23/25现成比例、标准误、CI、样本数；12个关联城市有至少一年度数据。5个请求返回空数组（Dallas、Fort Worth、Charlotte-Mecklenburg、Denver、Clark County），保留返回证据。学区数据不改称市民数据。统一长表保留3,711行，其中2,817个数值、889个Data not available（原码888888）、5个小样本抑制（原码333333，<30 respondents）；缺测和CI/SE均清为空，原码另列，宽表保留原字段。
- HRSA心理HPSA完整CSV快照，记录生成日2026-11-10；按所在县保存component，不把同一designation重复加总，不合并不同designation类型或把群体重叠人数相加。
- SAMHSA 2025心理机构名录XLSX/PDF、服务代码本；CH/AD明确接受17岁或以下。25城邮政城市匹配保留机构明细。这是邮政名称供给代理；纽约Queens非标准邮政城市名有漏匹配风险，18岁资格需YAD补充，未计算服务容量/可预约性。
- CDC PLACES 2025全国place CSV、完整字段元数据；25城全部宽表和成人各指标的粗率/调整率与CI。观测年份随指标来源变化，不能用作青少年结局。

| 来源 | 长表行数 | 关联城市覆盖 | 观测期/版本 |
| --- | ---: | ---: | --- |
| S08 | 666 | 24/25 | 2021、2022、2023、2024、2025 |
| S08-api | 625 | 25/25 | 2021、2022、2023、2024、2025 |
| S08-state-NY | 20 | 1/25 | 2021、2022、2023、2024 |
| S08-state-CA | 100 | 4/25 | 2021、2022、2023、2024、2025 |
| S08-local-Chicago | 5 | 1/25 | 2021 |
| S08-local-Phoenix | 5 | 1/25 | 2021 |
| S08-local | 1 | 1/25 | 2024 |
| S09 | 500 | 25/25 | 2021、2022、2023、2024 |
| S10 | 4,920 | 25/25 | 2021、2022、2023、2024、2025 |
| S12 | 3,711 | 12/25 | 2021、2023、2025 |
| S13 | 148 | 25/25 | 2026-11-10 snapshot |
| S14 | 25 | 25/25 | 2025 directory (2024 N-SUMHSS) |
| S15 | 2,000 | 25/25 | 2025 release; BRFSS observation year varies by measure |

## 出版版本缺口、补齐结果与边界

- FBI Table8年度匹配：{('2021', 'not_in_table8'): 9, ('2021', 'available'): 16, ('2022', 'available'): 24, ('2022', 'not_in_table8'): 1, ('2023', 'available'): 23, ('2023', 'not_in_table8'): 2, ('2024', 'available'): 24, ('2024', 'not_in_table8'): 1, ('2025', 'available'): 24, ('2025', 'not_in_table8'): 1}。Charlotte-Mecklenburg、Las Vegas Metropolitan、Metropolitan Nashville是关联警务辖区代理；尤其Las Vegas机构人口远超Census市人口，禁止用市人口作其犯罪率分母。Jacksonville在出版Table8缺行，但现行FBI月度API取得2021—2025各12月数据：2024 murder63、rape446、robbery638、aggravated assault4529，合计violent5676；2025合计5239。JSO较早2024行政报告59件classified murders（另8件待分类）另存，其分类时点与现行API不同，不覆盖替换。Local政府原文再分发许可未确认，建议只推事实提取、链接和日志，完整PDF暂本地留存。
- 州/地方独立统计：NY DCJS官方CSV取得2021—2024五个NYC县等价区的Index Crime及12个月报送字段，已按五县合计作为S08-state-NY；Phoenix官方2010—2022 SRS表取得2021全部四类及合计，但其homicide明确含过失杀人，另命名本地口径而不作标准murder。California DOJ官方1985—2025年度CSV与June2026代码本已下载，提取全部4个加州目标城2021—2025共20城年，100个分类值；2021 Los Angeles30956、San Jose4832、San Francisco4887暴力合计，四分类全部核对；SRS/IBR混合转换口径与未提供月覆盖字段已标明。Chicago官方2021报告四类总25979，单列aggravated assault7237与battery8369相加，排除地方violent subtotal中的17件人口贩运；其余旧Table8缺行优先由同版FBI月度API解决。FDLE新旧页面/精确FIBRS附件实际403/404，证据保存；JSO门户可下载的Persons/Property/Society汇总不能替代暴力四分类。
- `crime_city_year_source_choice.csv`提供全部125个city×year的显式来源选择：120个同版FBI完整年，4个2021州/地方四分类补充，Phoenix2021独立本地口径；124/125可用四分类，主共同窗口2022—2025全25城，2024/25可直接从同版现行API取数。AZ DPS官方reports页已下载200，明确Crime in Arizona年报2020以后停刊，改用TOPS；TOPS入口200但尚未取得可验证Phoenix2021四分类年度表，保留具体证据。
- 现行FBI月度API完整覆盖2022—2025全部25城；2021完整20城，五个不足12月的城保留月数与空年值。CA三个缺口和Chicago有独立州/地方年度四分类；Phoenix仅有含过失杀人的本地总口径，不能当标准暴力犯罪总量。
- YRBS只覆盖参与学区且不同年缺测，任何缺失不等于0；25城不具备统一学区调查样本。按年度使用覆盖矩阵/宽表；没有用州值或PLACES成人率填充。
- FARS已取得至2024，2025城市ARF尚未取得；全国早期估计不用于城市值。行人PER_TYP5、脚踏车6/7；2022分类变化需参考代码本后再作跨年解释。
- EPA县级监测并非所有城市相交县都有监测；多县观测不要简单加总AQI天数。CBSA背景保留区域与各年城市居民份额。Oklahoma City约99.988%居民属36420，84人/0.0118%属Shawnee微区43060；微区无AQI记录不等于城市缺失。2025年度表已发布但可能修订。
- HRSA为2026动态快照，不能标成2024；designation分数/人数保存在组件宽表，未用重叠组件构造全市短缺比例。
- SAMHSA按邮政名称匹配，需空间精确指标时再地理编码/点落边界；目录漏报及年龄范围不替换成零服务。

## 复现与下一步

`analysis/collect_safety_health.py`下载固定官方来源；`_more.py`、`_discover.py`记录后续官方附件/前端入口；`_fbi.py`解析官方signedurl（签名会过期，应重新请求，不复用已存签名）；`_agencies.py`获取官方ORI注册表；`_yrbs.py`获取现成调查统计；`_crime_api.py`下载全25城五类月度犯罪与人口参与度，`_crime_extract.py`生成月表/年度总量/分类加总核对；`_extract.py`按主节点cities/county/CBSA映射生成统一长表和宽表；`_crime_choice.py`生成125城年显式来源选择与主窗口资格；`_status.py`生成库存、访问日志及覆盖。其他已下载精确URL、时间、状态、大小和SHA256均在访问日志，可按日志重下；HTTP失败保留实际状态，原因未核不归因于云/实体电脑。

下一步：按警务/学区/市县边界质量筛选共同年份，以现行FBI同版月度数据构造完整性合格的年度犯罪表，处理未参与/缺测青少年调查；需要市界精确供给时再做SAMHSA点落界与HRSA tract叠合。大ZIP本地完整保留，Git路线由主节点确定。公开发现JS与过期签名URL已脱敏，原响应SHA与脱敏说明保留；125个月度数据请求不使用API key。原始前端JS仅用于发现公开下载接口，不属于研究数据；可不推送这些JS和过期signedurl响应。
