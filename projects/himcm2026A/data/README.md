# 25城全量数据包

本数据包用于“最适合高中生居住的城市”研究。候选池是Census Vintage2025人口前25城市条目，含官方balance口径；不是三个试点城市。七个领域分别保留，尤其经济可负担性与社会包容不合并。

先读项目的`DATA_COLLECTION_STATUS.md`、`DATA_GAPS.md`，再读`metadata/cities.csv`。数值不是最终评价得分，没有生成真实城市排名。

## 使用入口

| 文件/目录 | 内容 |
|---|---|
| `processed/observations_all_levels.csv.gz` | 统一长表。包含城市、关联机构、学校、县/都市区背景及不同年份；保留来源与限定，不是可直接一列相加的指数矩阵 |
| `metadata/city_source_numeric_coverage.csv` | 全25城×来源的有效数值数量；0表示没有该来源有效数值，不表示指标为零 |
| `metadata/city_source_period_coverage.csv` | 细分年份、地理层级的覆盖统计 |
| `metadata/city_indicator_period_coverage.csv` | 25城×字段×年份×地理层级；单元格为有效数值数/记录总数，0/0表示无记录 |
| `metadata/observation_dictionary.csv` | 来源—字段—单位—地理层级字典与覆盖 |
| `metadata/cities.csv` | 冻结的25城与排名、人口、Census代码 |
| `metadata/city_county_crosswalk.csv`、`city_county_cbsa_crosswalk.csv` | 2020—2025居民分县人口及份额、CBSA匹配 |
| `extracted/foundation/acs/` | ACS全部城市原字段、MOE、相关县社区储备；五年是期间估计 |
| `extracted/education_inclusion/` | 两版CRDC全部相关学校/LEA模块、CCD会员/年级、毕业率与分组、HRC和Profiles |
| `extracted/safety_health/` | 犯罪机构/年月、FARS事故与死亡人员、空气、健康调查与资源 |
| `extracted/mobility_opportunities/` | SLD空间代理、公交机构、图书馆系统/网点、州补充、公园事实 |
| `extracted/foundation/costs/` | BEA分项与HUD卧室规格、ZIP储备 |
| `extracted/foundation/opportunity/` | 历史外部验证与2010/2020地理转换储备 |
| `extracted/policy_parameters/` | 25城青年票价与资格、DC政策、工资/调查/招生储备 |
| `metadata/*/STATUS.md` | 各域实际版本、缺口、清洗和解释 |
| `raw/` | 实际取得的源文件；发布与未发布范围以归档清单为准 |

## 必须保留的含义

`value`为空与0不同。`raw_value`、缺失码、抑制区间、MOE/置信区间保留在统一表或对应源表。`observation_period`、`geography_type`、`source_geo_id`、`quality_note`与数值一起使用。CSV中的地理代码必须按字符串读取，以保留前导0。

同一事实可有原字段、派生比例、不同边界或不同发布版本的表示；总行数不是独立样本数。不要把同一学校心理人员同时给教育和健康重复加分。多样性只是人口背景，HRC政策也不是所有高中生实际体验。

ACS派生比例附分子分母和组件MOE，未伪造协方差或派生置信区间。旧Urban毕业率中点是来源区间的代理，不能视为精确率或用于底线。CRDC负码、YRBS888888/333333、IMLS负码均未填0。

`analysis/integrate_collection.py`重新整合长表，原域脚本负责提取。下载记录提供原URL、时间、字节数、SHA256。从仓库根目录运行 `python projects/himcm2026A/analysis/restore_city_archive.py --extract` 可恢复完整包。大文本采用gzip；归档分块若存在，先运行项目的恢复脚本，按清单还原后再复算。受限源不会被恢复脚本擅自下载或发布。

归档包内的各域状态和早期上传记录是采集时快照；当前发布范围以仓库顶层 `DATA_COLLECTION_STATUS.md` 与 `metadata/source_file_publication.csv` 为准。大批量全国源文件可以从清单内原始URL重取，城市字段已随包保存。
