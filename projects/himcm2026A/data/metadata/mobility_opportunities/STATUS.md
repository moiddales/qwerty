# 自主出行与课外机会采集状态

实际采集日期：2026-11-11 UTC。城市池：`../cities.csv` 的全部25城。状态表为 `city_coverage.csv`；原始表实测行数见 `table_inventory.csv`，提取结果行数见 `extracted_inventory.csv`。

## 已取得的数据

| 来源 | 实际文件与规模 | 全25城结果 |
|---|---|---|
| EPA SLD V3 2021 | 全国CSV 220,740行、117列、201,568,176字节；两份官方方法指南；无损gzip 76,436,348字节 | 官方EPA空间服务与Census ACS2025边界选出两种BG集合；50,471行城市—BG—集合关系，50行覆盖诊断，200条四项环境代理 |
| IMLS FY2024 | ZIP 20,133,862字节，系统9,249行/190列，网点17,615行/37列；代码本 | 25城关联27个系统，保持系统层级；Fort Worth原表-3不作为0，已取得州源补充 |
| IMLS FY2023 | ZIP 3,679,038字节，系统9,252行/187列，网点17,586行/37列；代码本 | 与FY2024合计54系统年、1,919网点年；Fort Worth FY2023青少年活动仍缺 |
| Texas官方补充 | 2023、2025全表，2024 DataTool；2024 DataTool含现成24ARPrgms工作表 | 6个入选Texas城市，2024/2025共12系统年、48条活动观察。Fort Worth FY2024：986青少年活动场次、3,892出席人次；FY2025：1,133场、4,327人次 |
| FTA NTD | 2025单年Service 13,139行；2022—2025 Service 51,716行/69列；2025 Agency Information 2,897行/46列；Socrata字段元数据 | 25城主运营商关联表25行；四年服务明细4,136行；年度供给与客流观察1,551行。保留agency/mode/TOS，未分摊为城市总量 |
| BTS NTM | 2026-09-23快照schema与官方服务端聚合响应：站点1,263个agency/feed组，合计673,251源记录；线路1,131组，合计76,687源记录 | 25城均关联到主运营商或共享feed，站点/线路各33行。线路源记录可包含同路线的不同shape；不能直接解释为独立线路数 |
| TPL公开事实 | 2026排名PDF检查，2026设施XLSX仅内存检查；只保存25条10分钟步行公园覆盖的数字事实与引用 | 22条来自2026 PDF，3条为官方城市网页快照。没有归档或再分发TPL原始包、PDF、XLSX或完整网页 |
| Dryad独立调查 | DOI数据集JSON、版本文件清单JSON、公开落地页、从落地页提取README文字；CC0-1.0 | 已通过美国交通部NTL官方镜像取得CSV、XLSX与README，三文件SHA256均与Dryad清单一致；实际392数据行、129列，README称127变量的差异保留。API下载要求token，原网页403原因仍未确定 |

统一字段观察文件为 `data/extracted/mobility_opportunities/city_observations.csv`（711行）、`transit_observations.csv`（1,551行）和 `texas_library_program_observations.csv`（48行），合计2,310行。指标包含原始候选测量及不同年份/边界敏感性版本，不能当作2,310个独立评价指标。

## 影响解释的实际发现

1. **EPA CSV中的GEOID大量被写成截断科学计数法。** 提取脚本用完好的STATEFP/COUNTYFP/TRACTCE/BLKGRPCE拼接12位代码，验证220,740个代码唯一，并与空间服务返回代码全部匹配。GEOID20在SLD中指2019版BG，不指2020 Census BG；原始列保留于原文件。
2. **SLD空间值是明确的环境代理。** 官方ACS2025 place多边形在 `data/raw/mobility_opportunities/census_acs2025_city_polygons.json`，EPA按contains/intersects选择2019 BG。完全包含组与相交组分别人口加权；负值缺失码不计为0。边界部分BG人口未精确分摊，两组均值也不是严格数学上下界。Columbus、Houston等城的两组人口差异大，见覆盖表；不能把其中一组悄悄当作精确城市值。SLD底层人口/交通年份混合，且公交缺失包含距离阈值或GTFS覆盖问题。
3. **NYC分页已独立核验。** 首次复杂多边形分页出现重叠返回；改为无分页object-ID完整列表后逐千ID取属性，验证contained 6,224、intersecting 6,367条且无重复。最终提取使用 `epa_nyc_*_validated_*.json`，保留早先响应作访问证据。
4. **图书馆总量保留系统地理。** LSAGEOID/LSAGEOTYPE/LSAGEORATIO/GEOCODE和插补标志保留于宽表；多县、县、市外服务不全归总部城市。纽约包含NYPL branch libraries、Brooklyn、Queens三系统。YA定义为12—18岁同步活动，包含现场/线上，出席为人次。Fort Worth FY2024联邦表-3与州表有效值并列保存；不能据联邦缺失码断言现实图书馆停运。FY2023 Fort Worth程序值也缺，Denver HRS_OPEN两年缺。
5. **NTD数据源版本不混并。** 单年2025文件13,139行，多年文件中2025为13,043行；分别冻结原响应，以多年表用于跨年提取，不把两文件去重并成一个“更完整”年份。主运营商是有关联的供给背景，未声称穷尽每城全部提供者或给出放学后的站点覆盖。
6. **BTS共享feed不重复累加。** Phoenix对应feed的ntd_id含多个分号分隔机构；展开用于关联，全25城有记录，但原source_ntd_ids和feed_id保留，计数仍属于共享feed。
7. **TPL源内部需分版本。** 2026 PDF原图与文本均有Louisville行末写LasVegas的标签冲突；Columbus/Indianapolis未在该PDF识别。设施XLSX17页检查中Columbus仅Fields & Courts出现，未检到Indianapolis和LasVegas（North Las Vegas为另一城市）。改引官方城市页：Columbus71%、Indianapolis balance36%、LasVegas70%，标“网页快照、测量年份未确认”。Charlotte-Mecklenburg与Nashville-Davidson为county口径，与Census city/balance不同。TPL通用条款没有开放再分发授权，故仅引用少量数值事实，不能上传原表。
8. **访问失败按通道记录。** IMLS普通HTTP本次200，搜索浏览通道曾403；TPL城市页普通HTTP403、网页检索可读；Dryad元数据和落地页200、下载401/403。没有测试用户实体电脑，不作网络封锁归因。

## 还需解决的测量缺口

- 若SLD用于正式城市打分，需要官方细人口/精确空间分配以处理跨界BG；当前两集合用于环境代理和敏感性分析。
- 若图书馆/公交供给用于居民可获得机会，需机构服务区和跨市分配依据。已经保存现成系统与机构表，不按总部城市强制归属。
- 全25城青年票价与资格已在policy_parameters补齐；放学/周末具体站点可用性、活动价格与参与资格属于条件储备，尚未构造完整网络；NTD周末/工作日汇总已在服务宽表，不代替逐站时刻。
- TPL三城年份与两城边界仍异质；统一年份/边界应另核，当前未生成公园排名。
- Dryad调查已从NTL公开镜像补齐，见dryad_ntl_mirror_verification.json；原先下载失败日志保留。Texas 2024调查定义PDF入口本次404；保留州表YA列名，定义需与州现行问卷复核。

## 复现与归档

脚本均在 `analysis/collect_mobility_opportunities*.py`。下载器可读本目录 `download_*.json`；逐请求JSON记录URL、时间、状态、内容类型、大小、SHA256、版本、地理、许可说明及失败原因。官方空间请求含参数与原响应。顺序：下载全国表 → `..._spatial.py` → `..._nyc.py`（纽约完整ID验证）→ `..._extract.py` → `..._transit.py` → `..._texas.py`。

**不要把201MB未压缩 `epa_sld_v3_2021.csv` 加入Git。** 归档其无损gzip；`epa_sld_archive.json`同时记录原始/归档SHA256，已解压校验原始SHA一致。提取脚本若仅有gzip，先恢复同名CSV。所有其他原始文件当前均小于GitHub单文件100MB限制。当前子任务未执行git commit/push，由根节点集成。

验证：脚本语法检查通过；三份指标文件覆盖25城；EPA组件ID唯一且所选BG全部匹配；NY完整ID清单与提取数量一致；BTS全国聚合响应未触发transfer limit；下载的XLSX/ZIP/PDF/CSV已实际读取，国家与州图书馆记录保留差异。没有把未下载的Dryad数据登记为成功。

## 镜像补齐与跨域更新

2026-11-11：S27通过NTL ROSA P记录dot/86232公开ZIP镜像取得。新增dryad_ntl_*文件、独立请求日志、SHA256核对；原库存统计是补齐前快照，最终总清单由根项目生成。不能再把Dryad调查数据标为未取得。
