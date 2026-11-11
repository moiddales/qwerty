# 25城关联公交时刻补采

本批从MobilityData CC0目录定位官方运营商直链和显式公共镜像，保存35个feed，关联固定25城。纽约分公交公司/五区公交/地铁，洛杉矶、费城、DC分模式，Seattle含Metro与Sound Transit；其他必要机构仍须扩展，不能称穷尽全市服务。目录元数据的CC0不自动授权各原feed再分发。

`feed_registry_public.csv`保存原URL、镜像、许可入口、来源版本和范围。一个公开服务key参数在公开表中已脱敏，原始目录与完整registry只留本地。逐请求HTTP日志在`feed_logs/`及`http_requests.jsonl`，直接通道和镜像分别记账；原ZIP在`raw_local/current_gtfs/`。许可逐运营商核查，未确认的原件不进Git。

`feed_validation/`、`schedule_coverage.csv`、`validation_summary.json`记录关键表、关联、时区、频率服务和空时刻：35feed都具备非空agency/stops/routes/trips/stop_times，涉及36,701,900条stop_times，关键车次/站点/线路/日历关联检查通过。这是运营商时刻记录数，不是独立出行数或城市分数。Phoenix有frequencies模板，保留headway及exact_times；不能把模板当实际班次。空中间站时间保留用于路由阶段插值，不填午夜。

时效单独验收：参考2026-11-18周三、11-14周六、11-15周日。SFMTA mdb-2886与IndyGo ntd-50050现有包在三日均无服务，正在从新官方入口替换；不能凭非空表宣布25城当前时刻完整。Sun Metro原agency_timezone为America/Detroit，需与当地正式时刻和stop_timezone核对，暂不修改源值。当前快照不冒充2024基础窗口的历史时刻。

`denver_ntm_export_gap.json`复现官方NTM2024-12-02 ZIP含空stop_times.csv/目录，而gtfs-stats报告785035行；该包不计完整。后由RTD运营商当前直链取得完整2026包并验收。NTM单表CSV404、JSON大limit400等实际尝试保留，未把API/导出问题当现实无公交。官方NTL历史大ZIPRange请求返回206但读取超时，尚未取得可用历史包。

尚未完成：两城新包日期确认、必要多机构覆盖、学校/活动坐标与开放/年龄/收费资格的匹配、步行换乘和放学后/周末往返路由、原件再分发审查。所有25城继续保留；这里不产出可达性分数或排名。

复现脚本：`analysis/collect_transit_supplement.py`、`collect_transit_mirrors.py`、`validate_transit_supplement.py`。已下载文件保留为冻结快照，后续新版本另存并重新验收。
