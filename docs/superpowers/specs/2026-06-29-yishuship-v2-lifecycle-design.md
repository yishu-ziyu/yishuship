# yishuship V2 产品生命周期协议设计

> Historical note: this 2026-06-29 snapshot predates the JSON migration.
> The current canonical lifecycle entry artifact for new work is `product/00-product-type.json`; legacy `product/00-product-type.yaml` is migration fallback only.
> See `skills/.shared/product-lifecycle-21.md` for the current protocol.

## 背景

yishuship 当前定位是“在原版 Ship 基础上叠加 PM 能力的 AI 产品开发 harness”。现有 README 已把系统分成 PM 层与工程层：PM 层回答“做不做”，工程层回答“怎么做”。当前主流程是 `pm-intake → design → dev → e2e → review → qa → handoff`。

这条路线是对的，但当前 `pm-intake` 仍偏“PM 前置 + 工程交付”，没有把新沉淀的 21 个产品流程完整纳入系统。V2 的目标不是增加 21 个强制阶段，而是建立统一的生命周期协议：阶段负责推进，检查点负责不遗漏。

## 目标

把 yishuship 从“PM 前置的工程工作流”升级为“产品全生命周期工作流”。

成功标准：

- `/yishuship:pm-intake` 命令名保持不变，但内部升级为产品生命周期入口。
- 21 个产品流程被沉淀为生命周期检查点，而不是 21 个强制阶段。
- `pm_scorer.py` 从旧的杂项 63 维度调整为 `21 检查点 × 3 质量维度 = 189 分`。
- `/yishuship:auto` 同步理解新的 product lifecycle，但不强制每次都跑 growth。
- 路由、hooks、README、SkillOpt 文档统一使用 V2 语言。
- 旧 `.ship/tasks/<task_id>/pm/` 产物保持兼容，不直接失效。

## 非目标

- 不新增主命令 `/yishuship:product-lifecycle`。
- 不把 growth 强制塞进每次 `/yishuship:auto`。
- 不重构工程层 `design/dev/e2e/review/qa/handoff` 的内部执行逻辑。
- 不删除旧 `pm/` 目录兼容。
- 不引入 LLM judge 到 `pm_scorer.py`；评分保持可重复的 deterministic checks。

## 生命周期骨架

V2 生命周期为：

```text
Idea
→ Product Type 判断
→ Strategy Gate
→ Research Gate
→ Product Definition Gate
→ Product Specification Gate
→ Engineering Delivery
→ Release
→ Growth Loop
```

核心原则：idea 不直接进代码。idea 先变成产品判断，产品判断变成产品规格，产品规格变成工程任务，工程交付变成运营数据，运营数据反过来驱动下一轮迭代。

## 21 个产品检查点

21 个流程在 V2 中是 checkpoint，不是 phase。

```text
0. 产品类型判断
1. BRD：为什么值得做
2. MRD：给谁做、和谁竞争、为什么切换
3. 业务 / 场景调研
4. 现状梳理
5. 问题总结
6. 解决思路
7. 产品方案
8. 产品定位 / 核心流程 / 演进蓝图
9. 业务数据建模
10. 流程和角色
11. 界面设计
12. 报表设计
13. 数据埋点
14. 权限管理
15. 文档编写 / PRD
16. 技术方案
17. 项目管理
18. 研发 / 测试 / 上线
19. 运营管理
20. 迭代优化 / 数据分析
```

每个 checkpoint 用三个维度评分：

```text
presence：是否存在
有没有写清楚这个模块。

evidence：是否有证据
有没有用户、业务、数据、竞品、案例或明确上下文支撑。

actionability：是否可执行
能不能交给设计、研发、测试、运营继续推进。
```

## 产品类型分流

产品类型判断必须发生在生命周期入口处。B 端和 C 端不能使用同一套问题。

`product/00-product-type.yaml` 是后续 checklist 的入口：

```yaml
product_type: C | B | hybrid
primary_user:
buyer_or_user:
core_scene:
workflow_weight:
  strategy: required
  research: required
  data_model: required | optional
  permission: required | optional
  report: required | optional
  analytics: required
skip_rules:
  - checkpoint:
    reason:
```

C 端必须追问：

```text
用户为什么开始？
为什么继续？
为什么复用？
为什么分享或付费？
哪里流失？
核心行为闭环是什么？
```

B 端必须追问：

```text
业务流程怎么跑？
有哪些角色？
权限怎么分？
数据对象是什么？
报表给谁看？
风险怎么控制？
组织怎么协作？
```

第一版不做复杂配置引擎，只要求 `pm-intake` 在 `lifecycle-checklist.yaml` 中写出 required / optional / N/A 与原因。

## 标准产物目录

V2 标准 task layout：

```text
.ship/tasks/<task_id>/
  input/
    idea.md

  product/
    00-product-type.yaml
    01-strategy.md
    02-research.md
    03-problem-solution.md
    04-product-blueprint.md
    05-model-flow-role.md
    06-experience-spec.md
    07-data-permission-analytics.md
    08-prd.md
    09-tech-project-plan.md

  delivery/
    design-spec.md
    dev-context.md
    e2e-report.md
    review-report.md
    qa-report.md
    handoff.md

  growth/
    01-ops-plan.md
    02-data-analysis.md
    03-iteration-plan.md
    04-learning.md

  control/
    run_state.yaml
    lifecycle-checklist.yaml
```

兼容策略：产品层新产物写入 `product/`；工程层可继续使用现有 `plan/`、`e2e/`、`qa/` 等目录。需要时由 `delivery/design-spec.md` 映射到 `plan/spec.md`，避免打断现有 Ship 工程状态机。

## `/yishuship:pm-intake` 升级设计

命令名不变，内部从 PM Intake 升级为 Product Lifecycle Intake。

执行结构：

```text
Step 0：初始化
创建 task 目录、状态文件、生命周期清单。

Step 1：产品类型判断
输出 product/00-product-type.yaml。
决定哪些 checkpoint required、optional、N/A。

Step 2：战略与市场
输出 product/01-strategy.md。
覆盖 BRD + MRD。

Step 3：业务 / 场景调研
输出 product/02-research.md。
覆盖场景调研与现状梳理。

Step 4：问题与方案
输出 product/03-problem-solution.md 与 product/04-product-blueprint.md。
覆盖问题总结、解决思路、产品方案、定位、核心流程、演进蓝图。

Step 5：产品规格
输出 product/05-model-flow-role.md、06-experience-spec.md、07-data-permission-analytics.md、08-prd.md。
覆盖数据模型、流程角色、界面、报表、埋点、权限、PRD。

Step 6：技术与项目计划
输出 product/09-tech-project-plan.md。
覆盖技术方案与项目管理。

Step 7：交接工程层
输出 delivery/design-spec.md，必要时兼容写入 plan/spec.md。
进入 /yishuship:design → dev → e2e → review → qa → handoff。

Step 8：运营与学习，可选
输出 growth/*.md。
默认不强制每个小功能执行。
```

`pm-intake/SKILL.md` 只保留执行说明；完整方法论放在 `skills/.shared/product-lifecycle-21.md`，避免重复与漂移。

## `pm_scorer.py` 改造设计

旧心智：

```text
8 阶段 × 63 个杂项维度
```

新心智：

```text
21 个产品检查点 × 3 个质量维度 = 63 维度
63 × 3 分 = 189 分
```

保留现有公开函数，降低 SkillOpt 破坏面：

```python
score_stage(stage, output)
score_full_pipeline(outputs)
```

新增生命周期入口：

```python
score_lifecycle_artifact(checkpoint, text)
score_lifecycle_pipeline(outputs)
```

`score_full_pipeline()` 可以逐步代理到新结构，或保留兼容路径，但文档总分统一回到 189。当前 `docs/SKILLOPT_TRAINING.md` 中关于 arch-decision 后 202/204 分的漂移需要修正。

评分尽量用 deterministic rules：章节、证据词、URL、表格、字段、角色、指标、行动项、验收标准、风险与 owner。第一版不接入 LLM judge。

## 路由升级设计

`skills/use-yishuship/SKILL.md` 做三类改动：

```text
1. 修复所有 /yishuship:* → /yishuship:*。
2. 新功能 / 产品方向 → /yishuship:pm-intake → /yishuship:design。
3. 新增产品类型判断：C / B / Hybrid。
```

路由脑只负责选路，不负责承载 21 个 checkpoint 的全部细节。生命周期细节由 `pm-intake` 与共享协议承担。

## `/yishuship:auto` 升级设计

`auto` 文档和状态机入口同步理解 V2：

```text
pm-intake(product lifecycle) → PM Gate → design → dev → e2e → review → qa → handoff
```

Growth Loop 作为 handoff 后的 optional continuation。默认不强制进入主线，避免每个小功能都变成重流程。

当前 `scripts/auto-orchestrate.sh` 仍以 design 为第一执行 phase。V2 第一版可以先更新 auto skill 文档与初始化产物结构；是否把 `auto-orchestrate.sh init` 的第一 phase 改为 `pm_intake` 应谨慎处理。如果脚本改动过大会影响稳定性，先让 `/yishuship:auto` 明确要求已跑或即将跑 `pm-intake`，并通过 PM Gate 阻止跳过关键产品产物。

## Hooks / scripts 升级设计

现有 `pm-gate.sh` 与 `pm-verify.sh` 检查旧文件：

```text
pm/01-discovery.md
pm/02-definition.md
pm/03-design.md
pm/04-validation.md
```

V2 关键 gate 改为优先检查：

```text
product/00-product-type.yaml
product/01-strategy.md
product/03-problem-solution.md
product/08-prd.md
product/09-tech-project-plan.md
```

兼容策略：

```text
优先检查 product/*。
如果 product/* 不存在，再 fallback 到旧 pm/*。
```

进入工程层不要求 21 个 checkpoint 全满分，只要求关键产品判断已存在、可追溯、可交接。

## 文件改动清单

新增：

```text
skills/.shared/product-lifecycle-21.md
```

重写 / 大改：

```text
skills/pm-intake/SKILL.md
benchmarks/pm_scorer.py
```

中改：

```text
skills/use-yishuship/SKILL.md
skills/auto/SKILL.md
scripts/pm-gate.sh
scripts/pm-verify.sh
README.md
docs/SKILLOPT_TRAINING.md
DEVLOG.md
```

可能小改：

```text
.claude-plugin/plugin.json
.claude-plugin/marketplace.json
AGENTS.md
```

## 验证计划

```text
1. rg 确认没有 /yishuship 残留。
2. python -m py_compile benchmarks/pm_scorer.py。
3. 用 sample outputs 跑 score_lifecycle_pipeline，确认 max=189。
4. 对 shell scripts 跑 bash -n；如果本机有 shellcheck，再跑 shellcheck。
5. git diff 人工检查：没有无关重构，没有删除旧兼容入口。
```

## 风险与处理

- 风险：一次改太多导致 auto 状态机不稳定。
  - 处理：工程层状态机不做大重构，先通过 PM Gate 和文档协议接入 lifecycle。

- 风险：21 checkpoint 让小任务变重。
  - 处理：checkpoint 支持 required / optional / N/A；growth 默认可选。

- 风险：旧任务目录失效。
  - 处理：hooks 和 docs 保留旧 `pm/` fallback。

- 风险：评分框架和 SkillOpt 训练文档不一致。
  - 处理：统一总分 189，并在 docs/SKILLOPT_TRAINING.md 中说明 V2 映射。
