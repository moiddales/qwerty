# HiMCM 2026 A：当前交接

> 最新检查点A-032（2026-11-14）：5.6 SMAA 抽样审计通过，模型代码与论文不变（报告 docs/smaa_sampling_audit_zh.md，脚本 analysis/model/run_smaa_sampling_audit.py）。抽样分布与论文描述一致；Seattle 第一 75.0% 可复现，换种子后为 75.2% ± 0.5%；改为在整个 Θ_S 上均匀抽样时为 79.3%。

> 检查点A-031（2026-11-12）：学习材料改为"总版 + 四人专用讲解"，均由 paper_explained/make_guides.py 从 paper_explained.md 生成，并对照原讲解版（git ed9e183，52 页）标出改动：讲解框标"本版更新"（改动句高亮）或"本版新增"，原文改动句与新公式高亮。输出 HiMCM2026A_guide_all_zh.pdf（62 页）、HiMCM2026A_member_A/B/C/D_zh.pdf（14/16/19/17 页）；按用户要求不含附一至附四；改动句用深橙色字标出（无底色，避免影响阅读）。修改记录 PDF：docs/HiMCM2026A_change_log_zh.pdf。重建：cd paper_explained && python make_guides.py。分工表的页码仍指不带标记的 58 页讲解版。

> 检查点A-030（2026-11-12）：按用户决定修改模型（删交通死亡底线、加 P6 安全 ≥ 1/7、Chicago 犯罪 960）并重跑全部脚本；三份审计报告的修改已全部写入论文。新结论：Seattle 第一（Θ_S 下 75.0%、前三 99.1%、后悔 0.151），New York 第二，Denver 第三，Chicago 第 7。论文 PDF 正文 25 页（已达上限）+ AI 报告。讲解版（58 页）、组员 B 讲解（19 页）、分工表（md/docx/在线版）已同步。提交前仍需填队号并核对 AI 报告。

> 检查点A-029（2026-11-12）：用户清单 10 项审计见 [docs/checklist_audit_zh.md](docs/checklist_audit_zh.md)。待团队决定：交通死亡底线删除或补理由；是否加"安全 ≥ 1/7"（会使 Denver 从第 2 降到第 4）；Chicago 犯罪口径（改后 Chicago 约第 6）。全部替换一起试排正文 25 页、已达上限。提交论文未改动。

> 检查点A-027（2026-11-12）：模型写法细节评估（两轮）见 [docs/model_detail_audit_zh.md](docs/model_detail_audit_zh.md)：严重 2 处（5.6 SMAA、5.7 ELECTRE III 无法据论文复现）、中等 10 处、小问题 18 处、新闻稿措辞 1 处；唯一需改的数字是 Denver 置信因子 68.9%→66.7%。报告附可直接替换的英文文本，全部替换（含小问题，见报告第七部分与 docs/audit_minor_fixes.py）一起试排后正文 24 页、新闻稿 2 页。提交论文尚未修改，等待用户决定；Chicago 犯罪口径问题仍待定。

> 检查点A-024（2026-11-12）：新增论文中文讲解版 [paper_explained/HiMCM2026A_paper_explained_zh.pdf](paper_explained/HiMCM2026A_paper_explained_zh.pdf)（52页，原文逐段后接中文讲解，课程外知识见补充知识卡K1–K20），源文件 paper_explained/paper_explained.md，重建：cd paper_explained && python build.py。它是独立副本，提交用论文仍是 paper/ 下的文件；原论文再改时讲解版需手动同步。

> 检查点A-023（2026-11-12）：两轮论文逻辑审计已完成并修正（见 PROJECT_LOG A-022、A-023；Seattle 的领先在统一非特许学校口径（57% 对 31%）和联合可行性口径（47% 对 38%）下缩小但保持；检验脚本 analysis/model/run_audit.py → results/logic_audit.txt）。Seattle 在 Θ_S 下的领先依赖 Denver 的 2020–21 毕业率，已在论文第 8.3、10 节写明。论文见 [paper/HiMCM2026A_paper.pdf](paper/HiMCM2026A_paper.pdf)（正文22页含摘要、目录、两页新闻、参考文献；另附1页AI使用报告不计页数）。源文件 paper/paper.md、ai_report.md；重建：cd paper && python build.py <队号>（需 markdown、Node.js+Playwright、联网字体与MathJax）。提交前填写队号并核对AI使用报告。模型结果见 [MODEL_RESULTS.md](MODEL_RESULTS.md)。

> 最新检查点A-012：A-011已通过GitHub连接器同步为acda247并由Git取回验证。A-012包含25城工资/教育局部事实/活动心理样本，GTFS与历史缺口验证，仍在连续补采。读取supplement_20261111/city_task_tracker.csv与各域README；不要把25城有样本/非空表当完整实际机会矩阵。后续重点是未核招生与AP/IB、过期feed替换与必要联程、往返/活动窗口、新毕业率和未解决历史字段。

> 本地接管更新（2026-11-11 Asia/Shanghai）：指定分支起点1db1364；本机完整归档恢复与25城覆盖验收通过。未发现旧supplement/GTFS/NHTS文件。新补采实际成果在 `supplement_20261111/`，NHTS2022 V2.1已下载解析验证，招生/课程与活动/心理服务正在逐城落盘；公交、工资、毕业率和历史缺口继续实施。整体数据采集仍未完成。当前子代理按U20261111-13/14使用gpt-6.1-sol、xhigh，最多三个。


> 2026-11-11 本地迁移交接：先读 [LOCAL_CODEX_HANDOFF.md](LOCAL_CODEX_HANDOFF.md)，启动提示词见 [LOCAL_CODEX_PROMPT.txt](LOCAL_CODEX_PROMPT.txt)。当前为基础数据归档完成、关键补采未交付；尚无真实城市排名。前一异常会话的 23 城 GTFS / NHTS 下载汇报尚未恢复为可验证文件。本次仅编写迁移材料，未继续补采。

> 2026-11-11补采更正：此前“全量采集完成”的表述过宽。既有25城基础数据归档已完成，但招生资格/边界、细化公交时刻、活动参与条件、心理服务可用性和青年工资等仍待补采；已恢复采集，当前整体状态为进行中。下方旧完成记录仅对应已归档的基础批次。

更新时间：2026-11-11（Asia/Shanghai）。全25城约定范围的实际采集、缺口补查、统一提取和GitHub归档已完成；从远端重新取回核验通过。未计算城市排名。

## 接手顺序

1. 根AGENTS.md、USER_REQUESTS.md、根PROJECT_LOG.md。
2. PLAN.md与MATH_MODELS.md：七领域分开、原始不可补偿底线、分段价值、稳健偏好/SMAA；不用故意错误的v1。
3. DATA_COLLECTION_STATUS.md、DATA_GAPS.md、data/README.md。
4. data/metadata/source_acquisition_status.csv、city_source_numeric_coverage.csv及各域STATUS。

## 当前真实状态

- 仓库moiddales/qwerty，分支claude/affectionate-mayer-ihqczh。用户已授权持续采集与推送，每次重大更改必须记录要求原文、日期、修改、验证和接手动作；无需再次确认。
- 全25城已按Census V2025冻结。数据目录含人口/地域、53份ACS表、两版CRDC、CCD、毕业率、FBI五年、FARS四年、空气/健康、公交/图书馆/公园、BEA/HUD、HRC/DC政策和独立验证。
- 毕业率共同年资料可用性覆盖25城，但学校/LEA/市界不同；犯罪2022—25全25城同版完整；Phoenix2021仍为独立本地口径。
- 25城青年公交价格和条件已核实；Dryad调查从NTL官方镜像取得，SHA与Dryad完全一致，实际392行129列。
- 统一长表约15.7万行，包含原字段、派生量、多版本、多地理层级，不能当作独立样本或直接加权评分矩阵。
- 原始全国大包与版权/许可受限文件不等于城市字段包。实际归档范围与每个文件SHA见city_data_archive.json；未打包全国文件仍有精确URL/版本/哈希/提取脚本，SEDA原包/子集不发布。

## 上传与恢复

完整数据提交：`cddcc57e97e437d0d4f0651d71be63b57108f7de`。659个分块、86,295,630 bytes、1,201个成员文件。GitHub取回校验已通过，证据在`data/metadata/github_archive_verification.json`；SHA256：`08ef430a6018d6ff20c011333b5277b7a57b6eba15d1340cdf5fc033e78db20e`。

完整包manifest为`data/metadata/city_data_archive.json`，分块在`data/archives/city_data_parts/`。在仓库根目录恢复：

```bash
python projects/himcm2026A/analysis/restore_city_archive.py --extract
```

不要重新下载已经归档的城市数据。先读当前状态和逐文件发布清单，再选择数据。`.gitignore`排除展开文件、全国原包和缓存；小型可读表与可恢复分块已由Git跟踪。归档中的状态说明是采集时快照，仓库当前状态优先。

## 下一阶段

用真实数据计算时，对照 [RISKS.md](RISKS.md) 逐条检验并更新状态；已确认的条目是 M0 → M1 重大修订的候选。

先依据逐城质量表固定主分析的年份与指标，不按期望冠军挑年份。确定原始门槛和偏好情景后才运行实证模型。学校实际招生资格、逐站放学后/周末网络、活动费用与容量等保留为条件储备；不能把已保存入口当作完成了联合可行性模型。

各数据域的所有代码和方法细节在analysis/及data/metadata/*/STATUS.md。必要子代理仅用GPT6-Astra、最多三个同时运行；不重复已完成的全国下载。知识库相关指南本轮已读，继续按其“先数学问题再选模型”的原则实施。
