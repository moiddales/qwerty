# NHTS 2022 V2.1 公共微观数据

官方入口：https://nhts.ornl.gov/downloads 。下载链接从官方前端源码实际解析，Windows本机GET实测，详见 `http_requests.jsonl`。版本由代码本确认：V2.1，April 2025。

取得并解析：7,893 household、16,997 person、31,074 day-trip、16,997 long-distance、14,684 vehicle记录。原ZIP保留所有字段和Citation.pdf；`table_inventory.csv`记录逐表行列数与字节哈希，`field_dictionary.csv`枚举原字段。键与外键、正权重检查见 `validation.json`。14—18岁子集为979人、1,429条当日出行；年龄筛选不等于公立高中在读筛选。

HOUSEID标识家庭，HOUSEID+PERSONID标识个人。家庭权重WTHHFIN，个人WTPERFIN，当日出行WTTRDFIN；工作日/周末权重另列。用户指南PDF第33页明确STRATUMID作分层变量，以Taylor线性化估计方差，并明确NextGen不提供重复权重。权重报告PDF第35页解释该方差方法。不得套用独立同分布标准误。

实际CSV无州、县、城市、具名CBSA代码，保留Census区/分区、MSA类别与城乡分类；公开代码本核对一致。因此25城都记为`not_identifiable_in_public_use_file`，用于全国年龄出行背景，不制造逐城高中生估计。

代码本76页、用户指南35页及权重报告44页已下载、相关页文字核读。辅助PDF本地保存（其中权重报告标©Ipsos）；未确认第三方原件再分发权利，因此不提交辅助PDF，日志提供原URL、字节数、哈希及本地路径。公开使用数据ZIP、派生子集和字段事实单独发布。原负码不填零。

推荐引用（按原ZIP Citation.pdf）：Federal Highway Administration (2022), 2022 NextGen National Household Travel Survey Core Data, U.S. Department of Transportation, Washington, DC, https://nhts.ornl.gov/ 。

复现：从仓库根目录运行 `python -X utf8 projects/himcm2026A/analysis/collect_supplement_sources.py nhts`，再运行 `python -X utf8 projects/himcm2026A/analysis/validate_nhts_supplement.py`。

Git归档采用35个128KiB原始字节分块；从Git恢复先运行 `python projects/himcm2026A/analysis/restore_nhts_archive.py`，再运行验证脚本。原ZIP不重复作为大二进制入Git。
