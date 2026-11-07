# 调研：三模型推文溯源与同类项目对比

调研日期：2026-11-07。star 数取自当天的 GitHub 搜索结果。

## 1. 推文溯源：并不指向同一个仓库

起点是 [@maixbt 的推文](https://x.com/maixbt/status/2118352049268052071)。顺着这个账号的时间线和网络搜索，找到了以下同类推文：

| 推文 | 日期 | 内容 | 引用或链接 |
|---|---|---|---|
| [@mirku21](https://x.com/mirku21/status/2107939129736700335) | 10/07 | "Official Anthropic tip"，`claude --advisor opus --subagents haiku`，约 85.8 万浏览 | 官方 advisor 文档 |
| [@dr_cintas](https://x.com/dr_cintas/status/2107939634705559974) | 10/07 | 变体：Opus 规划，Sonnet 写代码，Haiku 只读，Fable 做 advisor | Haiku 5.5 发布推文 |
| [@stretchcloud](https://x.com/stretchcloud/status/2109347801369092603) | 10/11 | 借这个话题推广自己的 Campfire 仓库 | github.com/stretchcloud/campfire |
| [@LearnWithSubhan](https://x.com/LearnWithSubhan/status/2109704686542733762) | 10/12 | 和 mirku21 **逐字相同** | 官方 advisor 文档 |
| [@xsmryze](https://x.com/xsmryze/status/2116659187317186583) | 10/31 | `claude --model sonnet --advisor opus` | 官方 sub-agents 文档，以及一篇赞助文章 |
| [@maixbt](https://x.com/maixbt/status/2117686478264508758) | 11/03 | 同一套文案（第 1 次） | N01ennn 的赞助文章 |
| [@maixbt](https://x.com/maixbt/status/2118352049268052071) | 11/05 | 同一套文案（第 2 次） | Addy Osmani《Critical thinking when agents do the work》 |
| [@maixbt](https://x.com/maixbt/status/2118816638774493613) | 11/06 | 同一套文案（第 3 次） | N01ennn 的赞助文章 |

结论：

- **共同来源是官方文档，不是某个仓库。** 推文给出的链接是 [advisor](https://code.claude.com/docs/en/advisor) 和 [sub-agents](https://code.claude.com/docs/en/sub-agents) 这两页。
- **被引用的文章都不讲这套配置。** Addy Osmani 那篇讲的是 agent 时代的批判性思维。推文里"600 行 PR 里有个默认值被翻转""新上下文的 subagent 自查""问一句 Did I miss anything?"这几处确实出自这篇。但"Haiku/Sonnet/Opus 分工"和"Opus 只醒三次"这两处在文中找不到。N01ennn 那篇是 Slack 机器人 Viktor 的付费合作文章。
- **夹带的推广内容。** 好几条推文提到 "JEV"，那是 TypeSafe 公司的付费分类服务，会把经过脱敏的 prompt 和 shell 命令发到外部 API。
- **编出来的细节。** 官方文档里没有 `--subagents` 参数。"一位 Anthropic 工程师分享"是把 Addy 的文章套到了这套配置上。

## 2. 官方文档要点

**Advisor**（[文档](https://code.claude.com/docs/en/advisor)）

- 开启方式：`/advisor opus`、在 settings 里写 `"advisorModel": "opus"`（任何层级的 settings 文件都可以），或者用 `claude --advisor opus`。
- 它是服务端工具，能看到**完整对话**，包括每一次工具调用和结果。
- 调用时机："Claude decides when to call the advisor. It tends to consult before committing to an approach, when an error keeps recurring, and before declaring a task done, but the timing is model-driven rather than rule-based." 另外，"There is no setting to cap or force advisor calls." 推文里的"三个时刻"就出自这段话。
- advisor 的模型等级必须不低于主会话模型。
- 只在 Anthropic API 上可用。`DISABLE_TELEMETRY` 这类变量会让它静默关闭。

**Subagents**（[文档](https://code.claude.com/docs/en/sub-agents)）

- `model` 可以写 `sonnet`、`opus`、`haiku`、`fable`、完整模型 ID，或 `inherit`。
- 其他字段：`tools`、`disallowedTools`、`effort`、`omitClaudeMd`、`maxTurns`、`background`、`isolation: worktree`、`hooks`、`memory`。
- 模型优先级：调用时传入的 `model` > agent 文件里的 `model` > 环境变量 `CLAUDE_CODE_SUBAGENT_MODEL` > 主会话模型。设置 `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` 会强制所有 subagent 用同一个模型。
- **内置的 Explore 默认跟主会话用同一个模型**，不会自动用 Haiku。要换成 Haiku，得自己写一个同名 agent 覆盖它。
- 默认允许 subagent 再调用 subagent，最多 3 层，可以用 `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` 调整。所以本方案在所有只干活的 agent 上都禁用了 `Agent` 工具。

**Hooks**（[文档](https://code.claude.com/docs/en/hooks)）

- Bash 命令以非零状态退出时，触发的是 `PostToolUseFailure`。错误文本在 `error` 字段里，首行是 `Exit code N`。用户中断时 `is_interrupt` 为 true。这个事件的输出支持 `hookSpecificOutput.additionalContext`。
- Stop hook 的输入有 `transcript_path`、`stop_hook_active` 和 `last_assistant_message`。要拦截就输出 `{"decision":"block","reason":"..."}`。连续拦截 8 次后，Claude Code 会强制结束。

## 3. GitHub 同类项目对比

搜索方法：用 GitHub 的仓库搜索按 star 排序，关键词包括 claude code subagents、claude-code agents、multi-model、advisor opus、reviewer subagent 等。结果分成两类：一类是 star 很多的**通用合集**，另一类是 star 很少、但和推文做法**直接对应**的项目。两类都选了几个，克隆下来读了源码。

| 项目 | ⭐ | 模型分配（按 agent 文件里实际写的 `model:` 统计） | 审查机制 | 约束方式 | 备注 |
|---|---|---|---|---|---|
| [affaan-m/ECC](https://github.com/affaan-m/ECC) | 298,920 | 303 个带 model 的文件：Sonnet 242，Opus 33，Haiku 28。主目录 71 个 agent，Opus 只用于 architect、planner 等 | code-reviewer 跑在 **Sonnet** 上，描述写着"MUST BE USED for all code changes" | 约 28 个 hook，含多个 Stop 拦截。delivery-gate 用 `stop_hook_active` 保证最多拦一次 | 功能最全，但很重、侵入性强 |
| [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) | 113,840 | **不指定模型** | doubt-driven-development：新上下文、以推翻为目标审查，"需要的是成品和约定，不是过程"；code-review 里有变异检查（把条件反过来，测试仍然通过就是问题） | 靠 skill 和斜杠命令 | 作者就是被引用那篇文章的作者 |
| [wshobson/agents](https://github.com/wshobson/agents) | 42,278 | 202 个 agent：Sonnet 70，Opus 54，inherit 52，Haiku 24，Fable 2 | 3 个 Opus 审查员（code、architecture、security），由 `/full-review` 分阶段并行调用，中间有人工确认点 | 只能手动调用命令 | 分档文档写得最清楚 |
| [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) | 26,394 | 158 个：Sonnet 112，inherit 27，Haiku 19，**Opus 0** | code-reviewer 用 `inherit`，并且**带 Write 和 Edit 权限** | 没有约束 | README 说 security-auditor、architect-reviewer 用 Opus，**实际文件写的是 `inherit`** |
| [Nanako0129/pilotfish](https://github.com/Nanako0129/pilotfish) | 715 | 主会话 Opus。executor 和 mech-executor 用 Sonnet，scout 用 Haiku | plan-verifier 和 verifier 都是**新上下文的 Opus**，按风险触发。plan-verifier 返回 READY/REVISE；verifier 返回 CONFIRMED/REFUTED/INCONCLUSIVE，问题按 P0–P4 分级 | 工具白名单做硬只读（plan-verifier 只有 Read、Glob、Grep） | 唯一附 benchmark 的项目，也承认"自动分派不保证" |
| [AlessandroAnnini/claude-code-multi-model-team](https://github.com/AlessandroAnnini/claude-code-multi-model-team) | 0 | Sonnet 主会话 + `advisorModel: opus`，3 个 Haiku 侦察（Explore 覆盖版、grep、docs） | 只用官方 advisor | `omitClaudeMd`、`background`；JEV 版本附带一个 bash 拦截 hook | **和推文写法最接近的落地实现**。作者自己写明"没有 benchmark，触发时机不保证" |
| [Fredasterehub/kiln](https://github.com/Fredasterehub/kiln) | 225 | Fable、Opus、Sonnet 混用，另外接了 GPT | 用 plan-breaker 和 plan-judge 做对抗式计划审查 | — | 作者自标 RED："Nothing has been built end to end with this yet"，不建议参考 |

### 共同点

1. 便宜的模型只负责收集证据，不做决定。
2. 审查要独立于写代码的人：要么换模型，要么用新上下文，要么两者都换。
3. 都承认，只写在 CLAUDE.md 里的规则不能保证一定被执行。

### 主要分歧

| 维度 | 不同做法 |
|---|---|
| 主会话用什么模型 | Sonnet（推文、AlessandroAnnini、ECC） vs Opus（pilotfish、dr_cintas 的变体） |
| 审查员能看到什么 | 完整对话（官方 advisor） vs 只看计划和 diff（pilotfish、agent-skills、本方案的 verifier） |
| 什么时候触发 | 每次都审（ECC） vs 按风险触发（pilotfish） vs 手动命令（wshobson） vs 由模型自己决定（advisor） |
| 只读怎么保证 | 只靠提示词（VoltAgent 甚至给了写权限） vs 工具白名单（pilotfish） |
| 审查结论的格式 | 自由文本 vs 结构化结论 + 分级（pilotfish） |

### 本方案从每个项目借了什么

| 来源 | 借用的做法 |
|---|---|
| 官方文档 / AlessandroAnnini | `model: sonnet` + `advisorModel: opus`；写一个 Haiku 版 `Explore` 覆盖内置版本；`omitClaudeMd`；`effort: low` |
| pilotfish | 新上下文的 Opus verifier；三种结论 + P0–P4 分级；按风险触发；用 `disallowedTools` 做能力约束 |
| addyosmani/agent-skills 和 Addy 的文章 | 以"推翻"为目标；只给成品和约定、不给过程；列出"测试没证明什么"；变异式检查；最后问一句 "Did I miss anything?"；汇报时先给出实际命令和输出 |
| ECC | 用 Stop hook 做确定性门禁，并靠 `stop_hook_active` 保证最多拦一次 |
| 推文 | 三个时刻：计划定稿前、同一错误第二次、完成前 |

### 有意没有采用的

- JEV 和其他外部分类服务：会把数据发到外部，而且要付费。
- 上百个 agent 的大合集：会挤占上下文，也难以审计。
- 每次改动都用 Opus 审查：成本高，所以改为按风险触发。
