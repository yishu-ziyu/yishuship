# yishuship

> Ship 增强版：一个把 idea 推进到可交付结果的 PM + engineering delivery runtime。

yishuship 不是一组松散的斜杠命令。它把产品判断、需求澄清、架构选择、垂直切片、TDD 实现、双轴 review、运行时 QA、发布交接和复盘沉淀放进同一条工作链。

核心目标是超级个体式交付：用户给出一个想法，agent 能判断要不要做、定义清楚做什么、拆成可执行工程任务、实现、验证、交付，并把重要知识写回仓库。

[完整用法](docs/operations/yishuship-usage.md) · [SkillOpt 训练](docs/SKILLOPT_TRAINING.md) · [Matt flow 决策](docs/decisions/DEC-0004-matt-pocock-flow-standard.md) · [原版 Ship](https://github.com/heliohq/ship) · [SkillOpt](https://github.com/microsoft/SkillOpt)

## 当前状态

- 本机全局 skill 暴露面：`14/14`。
- Claude Code：`~/.claude/skills/yishuship:*` 和 Claude plugin cache 可用。
- Trae / agents：`~/.agents/skills/yishuship:*` 可用。
- Codex personal plugin cache：`~/.codex/plugins/cache/personal/yishuship/0.1.0` 可用。
- Matt Pocock upstream skills 已 vendor 到 `vendor/mattpocock-skills/`，并通过 phase runtime activation 和 `/yishuship:matt` 实际读取执行。
- SkillOpt held-out test：Matt flow 样本 hard=`1.0`，soft=`1.0`；整体 test split hard=`1.0`，soft=`0.9841`。

如果客户端已经开着但看不到新命令，重启当前 Claude Code / Trae / Codex 会话。

## 默认主链

```text
idea
  -> alignment / shared language
  -> PRD with test seams
  -> vertical slices
  -> TDD implementation
  -> two-axis review
  -> runtime QA
  -> handoff
  -> learning / next iteration
```

这条链来自三层能力：

| Layer | 作用 | 主要位置 |
|---|---|---|
| Product lifecycle | 判断做不做、做什么、为谁做、为什么现在做 | `skills/pm-intake/`, `skills/.shared/product-lifecycle-21.md` |
| Engineering delivery | 设计、实现、测试、review、QA、发布 | `skills/design/`, `skills/dev/`, `skills/e2e/`, `skills/review/`, `skills/qa/`, `skills/handoff/` |
| Matt upstream runtime | 把 Matt Pocock 的高质量工程 skills 作为真实运行标准 | `skills/matt/`, `skills/.shared/matt-pocock-standard.md`, `vendor/mattpocock-skills/` |

## Plugin 和 Skill 的关系

插件是分发和运行时外壳：它把 skills、hooks、脚本、vendor 标准层和同步逻辑一起安装到 Claude Code / Codex / agents 环境。

skill 是可触发的工作纪律：每个 `SKILL.md` 描述一种稳定流程，例如 `/yishuship:pm-intake`、`/yishuship:dev`、`/yishuship:matt`。

所以 yishuship 选择插件形式，是因为全流程不只是一个 skill 文档能解决的事。它需要：

- 多个独立入口，每个入口有清晰触发条件。
- hooks 和脚本约束阶段隔离、PM gate、stop gate。
- durable artifacts，把需求、决策、验证和交接写到磁盘。
- vendored upstream skills，让 Matt 的原始方法被读取执行，而不是靠改写后的摘要。
- benchmark env，用 SkillOpt 测试流程是否真的稳定触发。

## 怎么用

不确定走哪条路时，从路由脑开始：

```text
/yishuship:use-yishuship
```

清楚目标时直接调用对应 skill：

| Intent | Command | Result |
|---|---|---|
| 一个原始 idea、产品方向、新功能 | `/yishuship:pm-intake` | 产品类型、用户、问题、策略、调研、PRD、test seams、工程交接 |
| 想直接使用 Matt 原始流程 | `/yishuship:matt` | 读取并执行 vendored Matt `SKILL.md` |
| 已经想清楚方向，需要设计方案 | `/yishuship:design` | 对抗式设计、可执行 spec、vertical slices |
| 实现已有 plan / issue | `/yishuship:dev` | 按 slice 执行，读取 `implement` + `tdd` upstream |
| 固化验收测试 | `/yishuship:e2e` | E2E 测试、运行记录、回归证据 |
| 找 bug 或审查 diff | `/yishuship:review` | Standards + Spec 双轴 review |
| 跑真实应用做 QA | `/yishuship:qa` | 独立运行时验证和问题证据 |
| 改善架构或清理复杂度 | `/yishuship:refactor` | deep-module 扫描和 scoped refactor plan |
| 做详细系统设计 | `/yishuship:arch-design` | 设计文档、接口、边界、权衡 |
| 生成项目文档 | `/yishuship:write-docs` | `docs/` 下的结构化文档和索引 |
| 视觉系统 | `/yishuship:visual-design` | `DESIGN.md` 和预览 |
| 发布、PR、CI 修复、交接 | `/yishuship:handoff` | PR / CI loop / context handoff |
| 从 idea 到交付全流程 | `/yishuship:auto` | PM -> design -> dev -> e2e -> review -> qa -> handoff |

### Matt upstream 直接调用

```text
/yishuship:matt use ask-matt to choose the right workflow
/yishuship:matt use grill-with-docs for this idea
/yishuship:matt run to-prd on our conversation
/yishuship:matt use to-issues to split this PRD
/yishuship:matt use tdd for this issue
/yishuship:matt use code-review on this diff
```

`/yishuship:matt` 不复制 Matt 的内容，也不只引用摘要。它会选择 `vendor/mattpocock-skills/**/SKILL.md`，完整读取后在 yishuship 的产物约定里执行。

## 它会产出什么

重大任务默认写到：

```text
.ship/tasks/<task_id>/
  input/
  product/
  delivery/
  plan/
  e2e/
  qa/
  control/
  dev-context.md
```

长期知识写到：

```text
CONTEXT.md
docs/decisions/DEC-NNNN-*.md
docs/operations/
docs/design/
```

重要原则：不要把关键项目知识只留在聊天里。

## 安装和同步

本仓库的默认本地路径：

```text
/Users/mahaoxuan/Developer/yishuship
```

检查 Claude Code 暴露面：

```bash
scripts/sync-local.sh --check
```

检查远端和本地是否一致：

```bash
scripts/sync-local.sh --check-remote
```

修复 Claude Code plugin cache 和 `~/.claude/skills/yishuship:*` 链接：

```bash
scripts/sync-local.sh --apply
```

检查或修复 Trae / agents 的 skill 链接：

```bash
CLAUDE_SKILLS_DIR="$HOME/.agents/skills" scripts/sync-local.sh --check
CLAUDE_SKILLS_DIR="$HOME/.agents/skills" scripts/sync-local.sh --apply
```

健康状态应包含：

```text
skill_links: 14/14
update_needed: no
```

## 验证

基础结构检查：

```bash
find skills -name "SKILL.md" | wc -l
```

期望值是 `14`。

Matt runtime activation 检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=benchmarks \
  python3 -m unittest benchmarks/test_matt_runtime_activation.py
```

PM scorer / lifecycle 回归：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=benchmarks \
  python3 -m unittest benchmarks/test_pm_scorer_lifecycle.py
```

完整 SkillOpt held-out eval：

```bash
git clone https://github.com/microsoft/SkillOpt.git /tmp/SkillOpt
scripts/sync-skillopt-env.sh /tmp/SkillOpt
cd /tmp/SkillOpt
python scripts/eval_only.py \
  --config configs/yishuship/default.yaml \
  --skill skillopt/envs/yishuship/skills/initial.md \
  --split test
```

## SkillOpt 测什么

yishuship 的 SkillOpt env 不是只测文案。它会产生 rollouts，再按两种 scorer 评分：

- 普通 PM 样本走 `pm_scorer`：检查产品生命周期、证据、可执行性。
- 带 `expected_flow` 的样本走 `matt_flow_scorer`：硬测 Matt 主链节点是否被触发。

Matt flow required nodes：

```text
alignment
shared_language
prd_test_seams
vertical_slices
tdd
two_axis_review
handoff
prototype
diagnosis
deep_module
```

这让“Matt 的能力是否真的活起来”变成可测矩阵，而不是 README 里的声明。

## 仓库结构

```text
skills/
  use-yishuship/    router
  matt/             Matt upstream runtime adapter
  pm-intake/        product lifecycle intake
  design/           adversarial design
  dev/              implementation + peer verification
  e2e/              durable acceptance tests
  review/           standards + spec review
  qa/               runtime QA
  refactor/         architecture health scan
  handoff/          PR / CI / context handoff
  arch-design/      detailed system design
  visual-design/    DESIGN.md
  write-docs/       docs generation
  .shared/          shared standards and gates
hooks/              Claude / Codex / Cursor hooks
scripts/            sync, gate, orchestration, SkillOpt sync
benchmarks/         pm_scorer, matt_flow_scorer, SkillOpt env
docs/               decisions, operations, specs
vendor/
  mattpocock-skills/  Matt Pocock Skills For Real Engineers snapshot
```

## 与原版 Ship 的区别

| Dimension | Ship | yishuship |
|---|---|---|
| 定位 | 工程 harness | PM + 工程 + 交付 runtime |
| 入口 | `/ship:use-ship` | `/yishuship:use-yishuship` |
| 新功能 | 直接进入 design | 先进入 product lifecycle |
| 产品判断 | 弱 | 做不做、为谁做、为什么做、怎么验证 |
| 工程主链 | design -> dev -> review | alignment -> PRD -> slices -> TDD -> review -> QA -> handoff |
| 上游标准 | 无 | Matt Pocock upstream runtime |
| 质量评测 | 无 | SkillOpt PM scorer + Matt flow scorer |
| 产物沉淀 | `.ship/` | `.ship/` + `CONTEXT.md` + decisions + operations docs |

## License

MIT。

`vendor/mattpocock-skills/` 保留上游 Matt Pocock skills 的 MIT license 和原始文件结构。
