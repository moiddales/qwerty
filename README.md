# qwerty：Claude Code 三模型协作 + 独立审查方案

主会话用 Sonnet 写代码，Haiku 只读侦察，Opus 负责把关。

这套配置可以直接复制到项目里使用。它综合了 X 上流传的"三模型"推文、Claude Code 官方文档，以及 GitHub 上 7 个同类项目的做法。调研过程和逐项对比见 [docs/research.md](docs/research.md)。

> 一句话来源：推文里的做法并不来自某个"神秘仓库"。它来自 Claude Code 官方的 **advisor 功能**（`advisorModel`），加上 **subagent 的 `model` 字段**。本仓库在这个基础上补了两样推文没有的东西：一个**只看计划和 diff 的新上下文审查员**，以及**用 hook 把软规则变成硬约束**。

## 四层结构

| 层 | 组件 | 模型 | 看到什么 | 作用 |
|---|---|---|---|---|
| 1 | 主会话 | Sonnet（`"model": "sonnet"`） | 全部 | 推理、写代码、做最终决定 |
| 2 | `Explore`、`callsites`、`tests` 三个 subagent | Haiku，effort low | 只看分派给它的任务，不读 CLAUDE.md | 找代码、查调用点、跑测试并原样返回输出，保持主上下文干净 |
| 3a | advisor（官方服务端工具） | Opus（`"advisorModel": "opus"`） | **完整对话** | 主会话拿不准时请教；调用时机由模型自己决定 |
| 3b | `verifier` subagent | Opus，新上下文 | **只看 `.claude/plan.md` 和 diff** | 以"推翻它"为目标审查计划和改动，结论是 CONFIRMED / REFUTED / INCONCLUSIVE，问题按 P0–P4 分级 |
| 4 | 两个 hook | 不用模型，确定性脚本 | hook 输入和 git | 同一错误第二次出现时提醒先查根因；大改动没审查就拦截一次"完成" |

3a 和 3b 是互补的：advisor 信息最全，但容易被主会话的推理带偏；verifier 没参与写代码，只看结果，更独立。

**只有非小改动才走计划审查和完成审查**（判断标准见 CLAUDE.md），小改动直接做，以免 Opus 成本失控。

## 文件

```
CLAUDE.md                         主会话规则：分派、计划审查、重复失败、完成审查
.claude/settings.json             主模型、advisor、hook 接线
.claude/agents/Explore.md         Haiku · 仓库地图（覆盖内置 Explore，内置版默认跟主会话同一模型）
.claude/agents/callsites.md       Haiku · 定义、引用、调用点
.claude/agents/tests.md           Haiku · 跑测试，原样返回命令、退出码、失败输出
.claude/agents/verifier.md        Opus · 新上下文，以推翻为目标的审查
.claude/hooks/repeat_failure.py   PostToolUseFailure(Bash)：同一错误第二次出现时提醒
.claude/hooks/review_gate.py      Stop：≥40 行改动且最后一次编辑后没跑 verifier → 拦截一次
.claude/.gitignore                忽略 hook 状态和每次任务的 plan.md
tests/test_hooks.sh               12 个场景的 hook 回归测试
docs/research.md                  推文溯源、官方文档要点、7 个仓库对比
```

## 安装

### 前置条件

| 要求 | 原因 |
|---|---|
| Claude Code ≥ 2.1.293 | `haiku` 别名要在这个版本以上才会解析到 Haiku 5.5；`omitClaudeMd` 需要 ≥ 2.1.271 |
| Anthropic API 或 Claude 订阅 | advisor 是服务端工具，**Bedrock、Vertex、Foundry 不可用**，不可用时会静默跳过 |
| `python3` 在 PATH 里 | 两个 hook 都是 Python 写的，只用标准库 |
| **不要**设置 `DISABLE_TELEMETRY`、`DO_NOT_TRACK`、`CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`、`CLAUDE_CODE_DISABLE_ADVISOR_TOOL` | 前三个会关掉功能开关拉取，advisor 会静默失效；最后一个直接禁用 advisor |
| 检查 `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` 和 `CLAUDE_CODE_EFFORT_LEVEL` | 前者让所有 subagent 忽略自己的 `model`，后者覆盖每个 agent 的 `effort` |

### 方式 A：装到某个项目（推荐）

把下面这些复制到目标项目根目录：

```bash
cp -r CLAUDE.md .claude tests /path/to/your-project/
```

如果目标项目已经有 `CLAUDE.md` 或 `.claude/settings.json`，就**合并**，不要覆盖：把本仓库 CLAUDE.md 的 "Model routing and verification" 一节追加进去，把 `settings.json` 里的 `model`、`advisorModel`、`hooks` 合并进去。然后在项目里跑一遍测试：

```bash
bash tests/test_hooks.sh
```

### 方式 B：对你所有项目生效

把 `agents/` 和 `hooks/` 放进 `~/.claude/`，把 CLAUDE.md 那一节追加到 `~/.claude/CLAUDE.md`。hook 路径要从 `${CLAUDE_PROJECT_DIR}/.claude/hooks/...` 改成 `~/.claude/hooks/...`。hook 状态会写到当前项目的 `.claude/state/` 下，记得在项目里忽略它。

### 验证

1. 在项目里启动 `claude`，横幅里应该出现 Advisor Tool 已开启的提示。也可以输入 `/advisor` 查看当前设置。
2. 输入 `/agents`，确认 `Explore`、`callsites`、`tests` 显示为 haiku，`verifier` 显示为 opus。
3. 布置一个跨文件的任务，观察流程：先写 `.claude/plan.md` → 用 verifier 审计划 → 等你说开始 → 写代码 → 跑测试 → 用 verifier 审 diff → 回答"Did I miss anything?" → 汇报。

## 已知局限（如实说明）

- **CLAUDE.md 是软规则，advisor 的时机由模型决定。** 官方原话是 "model-driven rather than rule-based"，也没有任何设置能强制调用 advisor。两个 hook 只保证了"重复失败会被提醒"和"大改动没审查不能直接收工"这两件事。
- **verifier 的只读只是部分硬性。** `Write`、`Edit`、`NotebookEdit`、`Agent` 被 `disallowedTools` 禁用了，但它保留了 `Bash`，因为要跑测试和 `git diff`。理论上它仍然能用 Bash 改文件，这一点只靠提示词约束。如果你要的是完全硬性的只读，可以删掉 `Bash`，代价是 verifier 只能读代码，不能自己跑测试。pilotfish 的 plan-verifier 就是这么取舍的。
- **项目里的 `"model": "sonnet"` 会改变所有打开这个项目的人的主模型。** 如果只想自己用，把它挪到 `.claude/settings.local.json`，或者启动时用 `claude --model sonnet`。
- **hook 只用模拟输入测过。** 输入字段按官方 hooks 文档编写：`PostToolUseFailure` 的 `error` 字段（首行是 `Exit code N`）和 `is_interrupt` 字段，Stop hook 的 `transcript_path`、`stop_hook_active` 字段和 `{"decision":"block"}` 输出。但这套配置还没在真实会话里端到端跑过。文档提到 transcript 可能落后于当前回合，最坏情况是多拦一次。Claude Code 自己也有保护：连续拦截 8 次后会强制结束。
- **review_gate 按改动行数判断"大改动"**，默认阈值 40 行，可以用环境变量 `REVIEW_GATE_MIN_LINES` 调整。它分不清 40 行文档改动和 5 行危险改动，风险判断仍然要靠 CLAUDE.md 里的定义。
- **省钱效果没有实测。** 调研的 7 个项目里，只有 pilotfish 附了 benchmark。上线前后建议用 `/usage` 对比一下。
- Windows 原生环境下需要把 hook 命令改成 PowerShell 能执行的形式，比如 `python "$env:CLAUDE_PROJECT_DIR\.claude\hooks\..."`。

## 卸载

删除 `.claude/agents/{Explore,callsites,tests,verifier}.md`、`.claude/hooks/`，以及 `settings.json` 里的 `hooks`、`advisorModel`、`model`，再删掉 CLAUDE.md 里对应的那一节。会话里也可以用 `/advisor off` 临时关闭 advisor。
