# HiMCM 2026 A：当前交接

更新时间：2026-11-11（Asia/Shanghai）。全25城实际采集、缺口补查与统一提取已完成；当前正在推送完整城市数据归档。未计算城市排名。

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

第一批远端提交d52b6d1b2f65715e5d31399b6647c2f0423412f2已由connector及git ls-remote核对。普通git push缺少认证；GitHub connector 7.46MB blob长期未返回，已停止该路线。128KiB base64分块、每批4块create_tree已验证成功，独立批次可并行建立不可变Git对象，最后一次更新分支。

完整包的manifest为data/metadata/city_data_archive.json，分块在data/archives/city_data_parts/。恢复命令：

```bash
python analysis/restore_city_archive.py --extract
```

只有全部part已推送且远端验证通过才可称归档上传完成。若会话中断，先看上传receipt与分支实际head，不能重开下载或声称已全部推送。已上传的不可变blob可以复用。

## 下一阶段

先依据逐城质量表固定主分析的年份与指标，不按期望冠军挑年份。确定原始门槛和偏好情景后才运行实证模型。学校实际招生资格、逐站放学后/周末网络、活动费用与容量等保留为条件储备；不能把已保存入口当作完成了联合可行性模型。

各数据域的所有代码和方法细节在analysis/及data/metadata/*/STATUS.md。必要子代理仅用GPT6-Astra、最多三个同时运行；不重复已完成的全国下载。知识库相关指南本轮已读，继续按其“先数学问题再选模型”的原则实施。
