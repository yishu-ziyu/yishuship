---
name: use-yishuship
description: >
  yishuship 路由脑：判断请求需要 PM 调研、单个 skill、phase bundle 还是全流程。
  在会话开始、用户说"做个功能"、意图模糊、架构选型、修复、QA、发布或全流程交付时使用。
allowed-tools:
  - Read
  - Bash
  - Agent
  - TodoWrite
  - AskUserQuestion
---

# yishuship: 路由脑

你是一个有产品判断力的超级个体。收到请求后，选择最小有用的路由。

## Activation Hard Rule (Detect → Enter → Announce)

Plugin value = executed constraints. Delivery work that never enters yishuship
state is a contract failure (see `docs/decisions/DEC-0005-activation-contract.md`).

1. **Detect** - run `bash scripts/yishuship-bootstrap.sh status` (or read the
   SessionStart `YISHUSHIP_STATUS` block). Prefer disk facts over chat memory.
2. **Classify** - use `next_action`:
   - `resume` → continue the active task first
   - `route` → pick a skill below, then enter
   - `idle` → enter only for delivery intents
   - `bypass_ok` → project opted out; stay L0 unless user asks for yishuship
3. **Enter / Resume** - for **delivery intents**, enter state **before any
   business source edits**:
   ```bash
   bash scripts/yishuship-bootstrap.sh enter "<short reason>"
   ```
   Equivalent: `/yishuship:pm-intake`, `/yishuship:auto`, or any path that
   creates `.ship/tasks/<task_id>/control/run_state.yaml`.
4. **Announce** when entered or resumed:
   ```text
   [yishuship] mode=<pm|design|dev|review|qa|e2e|handoff|auto|...> phase=<phase> task=<task_id>
   ```
5. **State Sense** - before executing, show the user `sense_report` from bootstrap
   `status` (or SessionStart `YISHUSHIP_STATE_SENSE`). Required fields:
   现在 / 缺什么 / 下一步 / 做完后(effect) / 你怎么确认(presentation) / 先感受(preview).
   Naked next steps without effect + presentation + preview are forbidden.
6. **Unknown Gate** - before routing into design/dev/arch (and again before any
   business source edit that relies on facts), read and apply
   `../.shared/unknown-gate.md`.
   Rule: **no citable evidence → unknown → research first** (or label
   assumption / ask user / BLOCKED). Confidence is not evidence.
   Mid-flight unknowns use light research (primary sources, repo read, observe).
   Product-shaped "should we build" unknowns still go through pm-intake research.

### Delivery intents (default-on)

New feature, product direction, architecture choice, design, implementation,
non-trivial fix, E2E, review-as-process, QA, refactor, handoff, full delivery.

For these: **state before business code**. Do not edit application/library
source until enter/resume has produced a `task_id` and you have announced.

### L0 bypass (explicit only)

Allowed without enter-state for:

- Pure Q&A / explanation with no repo delivery
- One-line / tiny local fix with no process need
- User explicitly says skip yishuship / quick fix only
- `next_action=bypass_ok` from project config

When bypassing a delivery-shaped request, announce:

```text
[yishuship] mode=L0_bypass reason=<one line>
```

Silent skip of delivery process is forbidden.

## Steps

1. Run bootstrap `status` (or read SessionStart `YISHUSHIP_STATUS`). If
   `next_action=resume`, continue that task before routing new work.
2. Read `.ship/ship-auto.local.md` and `.ship/pm-state.yaml` if they exist,
   because an active run beats a fresh route.
3. Read `../.shared/unknown-gate.md` (Unknown Gate). Scan the request for
   uncited claims (types A–F). If delivery work depends on unknowns, plan
   research before design/code; do not route as if those facts were settled.
4. For non-trivial product or engineering work, read `../.shared/matt-pocock-standard.md` and `../../vendor/mattpocock-skills/skills/engineering/ask-matt/SKILL.md` before choosing the route.
5. Classify the request as product, architecture selection, architecture detail, implementation, review, QA, E2E, refactor, docs, handoff, growth, conversation, or L0_bypass.
6. For delivery intents: enter state (bootstrap enter or equivalent) and announce before business source edits.
7. Present State Sense (`sense_report`) to the user; one next step with effect/presentation/preview.
8. Choose the lightest route that preserves quality.
9. If the route is ambiguous, ask one short question; otherwise dispatch or state the next skill directly.

## Execution Model (order / parallel / loops)

Read `../.shared/execution-model.md` before choosing multi-step routes.

```text
Layer 1  Stage dependencies   serial when required
Layer 2  Intra-stage work     parallel when safe
Layer 3  Failure              loop back, do not fake forward
```

- Do not open a stage whose upstream artifacts are missing.
- Prefer parallel **inside** design/dev (peer investigate, story waves), not
  parallel product-write + app-code-write as default.
- On fail: fix → re-run the failing check; after budget → BLOCKED/escalate.

When stating a route, include a short `[execution]` line:
`stage` / `dependency` / `parallel` / `loop`.

## Matt Flow Layer

Use Matt Pocock's vendored flow as the engineering architecture standard:

```text
alignment/shared language
→ PRD with test seams
→ vertical slices
→ TDD implementation
→ two-axis review
→ handoff
```

Route product ideas to `pm-intake`, not directly to implementation, because
`grill-with-docs` / `to-spec` alignment belongs before code. Route hard bugs
to diagnosis/dev only after there is, or can be built, a tight feedback loop.
Route codebase entropy to `refactor` or `arch-design` using the deep-module
vocabulary from the vendored `codebase-design` skill.

## 路由规则

**第一步：判断是不是新功能/产品方向**

如果请求涉及"加个功能"、"做个特性"、"我想实现"、"要不要做"——
这是产品决策，先走 PM Intake，不直接进工程。

```
新功能 / 产品方向 → /yishuship:pm-intake(product lifecycle) → /yishuship:design
Bug / 小修复      → /yishuship:review 或直接修
纯技术重构        → /yishuship:design (refactor scope)
运营 / 数据 / 复盘 → /yishuship:pm-intake Step 8 growth loop
不确定           → 问用户：这是新功能、修复、重构，还是增长复盘？
```

## 产品类型先判定

- C: 用户动机、留存、复用、分享、付费、流失、核心行为闭环
- B: 业务流程、角色、权限、数据对象、报表、风险控制、组织协作
- hybrid: 用户与购买者, checkpoint required/optional/N/A

pm-intake writes product/00-product-type.json.

## 完整路由表

| 请求 | 路由 | 说明 |
|------|------|------|
| "我想做个功能" / "加个特性" | `/yishuship:pm-intake` → `/yishuship:design` | **先调研再设计** |
| "帮我规划一下" | `/yishuship:design` | 对抗式设计 |
| "实现这个功能" | `/yishuship:design` → `/yishuship:dev` | 设计 + 实现 |
| "实现已有计划" | `/yishuship:dev` | 只做实现 |
| "检查这段代码" | `/yishuship:review` | bug 审查；有 fixed point/spec 时按 Standards + Spec 双轴 |
| "测试一下" | `/yishuship:qa` | 独立 QA |
| "加 E2E 测试" | `/yishuship:e2e` | 测试固化 |
| "发布" | `/yishuship:handoff` | PR + CI fix loop |
| "重构这段" | `/yishuship:refactor` | 四镜头扫描 |
| "全量交付" | `/yishuship:auto` | 完整流程 |
| "看看竞品" | `/yishuship:pm-intake` | 调研模式 |
| "做个产品" / "用 X 框架做" | `/yishuship:pm-intake` | **架构选型走 pm-intake** |
| "选个架构" / "用什么架构" | `/yishuship:pm-intake` | 架构选型决策（不直接做详细设计）|
| "做个系统设计" / "详细架构设计" | `/yishuship:arch-design` | **已知架构后的详细设计**（选型请走 pm-intake）|
| "写文档" | `/yishuship:write-docs` | 文档生成 |
| "设计视觉系统" | `/yishuship:visual-design` | DESIGN.md |

### 关键路由规则：架构选型 vs 架构详细设计

**架构选型**（"做什么形态、用什么架构"）走 PM 层：
- 触发词：选架构 / 用什么技术栈 / X 还是 Y / 单仓还是多仓
- 路由：`/yishuship:pm-intake`
- 产出：当架构未定时，在 `pm-intake` 阶段输出 `product/09-tech-project-plan.md`，若为长期决策则沉淀为 `DEC-NNNN.md`
- 理由：选错架构会导致后面所有工作重做，必须在 PM 层决策

**架构详细设计**（"已经定了 X 架构，现在做详细设计"）走工程层：
- 触发词：详细设计 / 系统设计 / ADRs / API 计划
- 路由：`/yishuship:arch-design`
- 产出：通过 `/yishuship:write-docs` 写 design 文档
- 前提：用户已经知道用什么架构，或上游 pm-intake 已经做完

**意图模糊时**，问用户：「这是要选架构（多个候选挑一个），还是已经定好架构做详细设计？」

不要默认跳过这一步——架构选型属于 PM 层决策，不属于工程层。

## 与原版 Ship 的区别

原版 Ship 是纯工程 harness。yishuship 在它前面加了一层 **PM 能力**：

```
原版 Ship:  需求 → 设计 → 实现 → 测试 → 发布
yishuship:  调研 → 判断 → 决策 → 设计 → 实现 → 测试 → 发布
            ─────────────
            PM 层（新增）
```

PM 层回答"做不做"，工程层回答"怎么做"。两层独立运作，PM 层在上，工程层在下。

## 默认选择

意图模糊时，路由到有界 bundle 而不是全流程：

- "帮我看看" → 先问"看什么？代码？竞品？还是产品方向？"
- "优化一下" → 先问"优化什么？性能？体验？还是代码质量？"
- "修一下" → `/yishuship:review` 找问题，再决定怎么修

## Completion Gate

Done means the next action is unambiguous **and causally closed**: a selected
`/yishuship:*` skill (or direct local fix / one blocking question), plus what
changes after it, how the user verifies, and a feel-first preview when possible.
Do not end with multiple equivalent options unless the user explicitly asks to
compare them.

Unknown Gate must not be violated on the way out: no delivery step may treat
uncited A–F claims as settled. If still unknown, the "done" output is research,
an explicit ASSUMPTION list, a user question, or BLOCKED — not fake certainty.

## [Router] Report Card

| Field | Value |
|-------|-------|
| Status | <ROUTED / ASK_USER / BLOCKED> |
| Intent | <product / architecture-selection / architecture-detail / implementation / review / QA / E2E / refactor / docs / handoff / growth / conversation> |
| Route | </yishuship:* or direct action> |
| Unknown Gate | <clear / research-first / ASSUMPTION / BLOCKED — cite or type A–F> |
| Effect | <what changes after this step> |
| Presentation | <how user verifies> |
| Preview | <smallest feel-first slice> |
| Reason | <one sentence> |
| Artifacts | <existing `.ship/tasks/<task_id>/` if relevant> |

## 产出物

所有产出物存放在项目的 `.ship/tasks/<task_id>/` 目录：

```text
.ship/tasks/<task_id>/
  input/idea.md             ← 原始灵感或需求
  product/*                 ← V2 产品生命周期制品 (含 00b-scope-challenge、00c-go-decision / Human Go)
  delivery/design-spec.md   ← 交付设计规格
  control/lifecycle-checklist.yaml ← V2 生命周期检查清单
  plan/*                    ← 兼容原版的工程计划文件 (spec.md, peer-spec.md, plan.md, diff-report.md)
  control/run_state.yaml    ← 工程状态机
  e2e/report.md             ← E2E 测试报告
  dev-context.md            ← 实现上下文
```

决策沉淀到项目的 `docs/decisions/DEC-NNNN.md`。
