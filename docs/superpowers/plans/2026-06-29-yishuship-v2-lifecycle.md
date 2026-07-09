# yishuship V2 Lifecycle Implementation Plan

> Historical note: this 2026-06-29 snapshot predates the JSON migration.
> The current canonical lifecycle entry artifact for new work is `product/00-product-type.json`; legacy `product/00-product-type.yaml` is migration fallback only.
> See `skills/.shared/product-lifecycle-21.md` for the current protocol.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade yishuship from a PM-fronted engineering workflow into a product lifecycle workflow built around 21 product checkpoints, while preserving existing command names and task compatibility.

**Architecture:** Add one shared lifecycle protocol document, then make `pm-intake`, routing, scoring, auto docs, and PM gates consume that shared vocabulary. Keep engineering skills and the existing auto state machine stable; bridge V2 product artifacts into the old Ship layout instead of rewriting the whole pipeline.

**Tech Stack:** Markdown skill docs, Bash hook scripts, Python deterministic scorer, existing yishuship plugin metadata.

**Execution note:** Do not commit during implementation unless the user explicitly asks. Use git diff checkpoints instead of commit steps.

---

## File Map

**Create**
- `skills/.shared/product-lifecycle-21.md` — canonical V2 lifecycle protocol, 21 checkpoint definitions, B/C/Hybrid routing, artifact layout, scoring semantics.
- `benchmarks/test_pm_scorer_lifecycle.py` — deterministic regression tests for the V2 scorer.

**Modify**
- `skills/pm-intake/SKILL.md` — keep command name, rewrite internals as Product Lifecycle Intake.
- `benchmarks/pm_scorer.py` — expose lifecycle scoring while preserving `score_stage()` and `score_full_pipeline()` public functions.
- `skills/use-yishuship/SKILL.md` — fix `/yishuship:*` pollution and route new product work into lifecycle intake.
- `skills/auto/SKILL.md` — document V2 full flow with product lifecycle and optional growth continuation.
- `scripts/pm-gate.sh` — prefer V2 `product/*` artifacts, fallback to legacy `pm/*` artifacts.
- `scripts/pm-verify.sh` — verify current V2 phase artifacts, fallback to legacy phases.
- `README.md` — update positioning, core architecture, skill table, scoring description, and task layout.
- `docs/SKILLOPT_TRAINING.md` — replace old score drift language with V2 `21 × 3 × 3 = 189` scoring.
- `DEVLOG.md` — add dated V2 design/implementation entry.
- `AGENTS.md` — update repository map to mention lifecycle protocol and `product/` artifacts.
- `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` — update description/keywords only if the old PM wording is present.

**Do not modify**
- `skills/design/`, `skills/dev/`, `skills/e2e/`, `skills/review/`, `skills/qa/`, `skills/handoff/` internals unless validation proves a broken reference.
- Existing `.ship/tasks/*` task outputs.
- Pre-existing dirty file `benchmarks/__pycache__/pm_scorer.cpython-313.pyc`.

---

### Task 1: Add canonical lifecycle protocol

**Files:**
- Create: `skills/.shared/product-lifecycle-21.md`

- [ ] **Step 1: Write the shared protocol document**

Create `skills/.shared/product-lifecycle-21.md` with this content:

```markdown
# yishuship V2 Product Lifecycle Protocol

This shared reference is the canonical source for yishuship's product lifecycle. Skills should link here instead of duplicating the full checklist.

## Core Principle

Do not turn 21 product processes into 21 mandatory phases. Use a small number of phases to move work forward, and use checkpoints to prevent product thinking from being skipped.

```text
Idea
→ Product Type
→ Strategy Gate
→ Research Gate
→ Product Definition Gate
→ Product Specification Gate
→ Engineering Delivery
→ Release
→ Growth Loop
```

## Standard Task Layout

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

## Product Type Gate

`product/00-product-type.yaml` decides which checkpoints are required, optional, or not applicable.

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

### C-side questions

- Why does the user start?
- Why do they continue?
- Why do they reuse it?
- Why do they share or pay?
- Where do they drop off?
- What is the core behavior loop?

### B-side questions

- How does the business process run today?
- Which roles participate?
- How are permissions split?
- What are the core data objects?
- Who reads the reports?
- How are risks controlled?
- How does the organization coordinate?

## 21 Checkpoints

| # | Checkpoint | Meaning | Main artifact |
|---|------------|---------|---------------|
| 0 | product_type | C / B / hybrid and skip rules | `product/00-product-type.yaml` |
| 1 | brd | Why this is worth doing | `product/01-strategy.md` |
| 2 | mrd | Who it serves, competitors, switching reason | `product/01-strategy.md` |
| 3 | scenario_research | Business / scene research | `product/02-research.md` |
| 4 | current_state | Current workflow and alternatives | `product/02-research.md` |
| 5 | problem_summary | Pain points, severity, evidence | `product/03-problem-solution.md` |
| 6 | solution_idea | Candidate solution logic | `product/03-problem-solution.md` |
| 7 | product_solution | Product shape and scope | `product/04-product-blueprint.md` |
| 8 | product_blueprint | Positioning, core flow, roadmap | `product/04-product-blueprint.md` |
| 9 | data_model | Business objects and relationships | `product/05-model-flow-role.md` |
| 10 | flow_role | Workflow, roles, handoffs | `product/05-model-flow-role.md` |
| 11 | interface_design | Key screens and states | `product/06-experience-spec.md` |
| 12 | report_design | Reports, viewers, decisions | `product/07-data-permission-analytics.md` |
| 13 | tracking | Events, metrics, data collection | `product/07-data-permission-analytics.md` |
| 14 | permission | Roles, access, risk controls | `product/07-data-permission-analytics.md` |
| 15 | prd | Requirements and acceptance criteria | `product/08-prd.md` |
| 16 | technical_plan | Architecture and technical choices | `product/09-tech-project-plan.md` |
| 17 | project_management | Milestones, owners, risks | `product/09-tech-project-plan.md` |
| 18 | delivery | Development, test, release evidence | `delivery/*` |
| 19 | operations | Launch and operation plan | `growth/01-ops-plan.md` |
| 20 | iteration_analytics | Data analysis and next iteration | `growth/02-data-analysis.md`, `growth/03-iteration-plan.md`, `growth/04-learning.md` |

## Quality Dimensions

Each checkpoint is scored on three dimensions, each from 0 to 3:

```text
presence      Does the checkpoint exist and contain concrete content?
evidence      Is it supported by user, business, data, competitor, case, or local-context evidence?
actionability Can design, engineering, QA, operations, or the next iteration act on it?
```

Total score stays compatible with the old 189-point frame:

```text
21 checkpoints × 3 dimensions × 3 points = 189
```

## Engineering Gate

Entering engineering should require only the minimum product handoff, not a perfect 189 score:

- `product/00-product-type.yaml`
- `product/01-strategy.md`
- `product/03-problem-solution.md`
- `product/08-prd.md`
- `product/09-tech-project-plan.md`

Existing legacy tasks with `pm/01-discovery.md`, `pm/02-definition.md`, `pm/03-design.md`, and `pm/04-validation.md` remain valid through fallback checks.
```

- [ ] **Step 2: Verify the shared protocol has no accidental old prefix**

Run:

```bash
cd /Users/mahaoxuan/Developer/yishuship
rg -n "yishuship" skills/.shared/product-lifecycle-21.md
```

Expected: no matches.

- [ ] **Step 3: Checkpoint diff**

Run:

```bash
cd /Users/mahaoxuan/Developer/yishuship
git diff -- skills/.shared/product-lifecycle-21.md
```

Expected: one new shared protocol document only.

---

### Task 2: Rewrite `pm-intake` as Product Lifecycle Intake

**Files:**
- Modify: `skills/pm-intake/SKILL.md`

- [ ] **Step 1: Replace `skills/pm-intake/SKILL.md` with the V2 workflow**

Use this full structure. Keep the frontmatter name `pm-intake`.

```markdown
---
name: pm-intake
version: 1.0.0
description: >
  Product Lifecycle Intake for yishuship V2. Keeps the /yishuship:pm-intake
  command name, but upgrades the internal workflow from a short PM preface into
  a full product lifecycle checkpoint system.
allowed-tools:
  - Bash
  - Read
  - Write
  - Agent
  - AskUserQuestion
  - TodoWrite
---

# yishuship: Product Lifecycle Intake

You are the product lifecycle owner. Your job is to turn an idea into a product handoff that engineering can safely execute.

Read `../.shared/product-lifecycle-21.md` before producing artifacts. Do not duplicate the whole protocol in this skill; use it as the shared source of truth.

## Hard Rules

- Keep `/yishuship:pm-intake` as the command name.
- Do not send an idea directly to code.
- Product type must be decided before strategy, research, PRD, or technical planning.
- Treat the 21 items as checkpoints, not as 21 mandatory phases.
- Mark each checkpoint as `required`, `optional`, or `N/A` with a reason.
- Growth artifacts are optional unless the user explicitly asks for launch, operation, data review, or next-iteration work.
- If the task is a tiny bug fix with no product decision, route to `/yishuship:review` or `/yishuship:dev` instead of forcing lifecycle intake.

## Step 0: Initialize

Create a task directory and state files:

```bash
TASK_ID=$(date +%Y%m%d-%H%M%S)
mkdir -p ".ship/tasks/$TASK_ID"/{input,product,delivery,growth,control,plan,e2e,qa}
cat > ".ship/pm-state.yaml" << EOF
phase: product-type
task_id: $TASK_ID
created: $(date -Iseconds)
workflow: product-lifecycle-v2
EOF
cat > ".ship/tasks/$TASK_ID/control/run_state.yaml" << EOF
task_id: $TASK_ID
active: true
current_phase: product-type
status: running
workflow: product-lifecycle-v2
updated_at: "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
EOF
```

Write the user's original idea to `.ship/tasks/$TASK_ID/input/idea.md`.

Create TodoWrite items:

1. Product type
2. Strategy and market
3. Research and current state
4. Problem and solution
5. Product specification
6. Technical and project plan
7. Engineering handoff
8. Optional growth loop

## Step 1: Product Type → `product/00-product-type.yaml`

Classify the product as `C`, `B`, or `hybrid`.

Ask only what is needed to classify. Prefer one question at a time.

Write:

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

Also write `.ship/tasks/$TASK_ID/control/lifecycle-checklist.yaml` with all 21 checkpoints and their `required`, `optional`, or `N/A` status.

Update `.ship/pm-state.yaml` to `phase: strategy`.

## Step 2: Strategy and Market → `product/01-strategy.md`

Cover checkpoints 1 and 2:

- BRD: why this is worth doing.
- MRD: who it serves, competitors, and why users would switch.

Required sections:

```markdown
## BRD: Why This Is Worth Doing

## MRD: Market, User, Competition

## Switching Reason

## Decision
- Do:
- Do not do:
- Evidence:
```

Update state to `phase: research`.

## Step 3: Research and Current State → `product/02-research.md`

Cover checkpoints 3 and 4:

- Business / scenario research.
- Current state and existing alternatives.

Required sections:

```markdown
## Scenario Research

## Current Workflow

## Existing Alternatives

## Evidence
```

For C-side products, include start / continue / reuse / share-or-pay / drop-off / behavior loop.

For B-side products, include process / roles / permissions / data objects / reports / risk / collaboration.

Update state to `phase: problem-solution`.

## Step 4: Problem and Solution → `product/03-problem-solution.md` and `product/04-product-blueprint.md`

`product/03-problem-solution.md` covers checkpoints 5 and 6:

```markdown
## Problem Summary

## Severity and Frequency

## Solution Idea

## Evidence

## Non-goals
```

`product/04-product-blueprint.md` covers checkpoints 7 and 8:

```markdown
## Product Solution

## Positioning

## Core Flow

## Evolution Blueprint

## Scope Boundary
```

Update state to `phase: product-spec`.

## Step 5: Product Specification → product spec files

Write four files:

```text
product/05-model-flow-role.md
product/06-experience-spec.md
product/07-data-permission-analytics.md
product/08-prd.md
```

`05-model-flow-role.md` covers data model and roles:

```markdown
## Business Data Model

## Object Relationships

## Workflow

## Roles and Handoffs
```

`06-experience-spec.md` covers interface design:

```markdown
## Key Screens

## Core States

## Empty, Loading, Error States

## Golden Journeys
```

`07-data-permission-analytics.md` covers reports, tracking, and permissions:

```markdown
## Report Design

## Tracking Plan

## Permission Model

## Risk Controls
```

`08-prd.md` covers the executable PRD:

```markdown
## Product Requirements

## Acceptance Criteria

## Edge Cases

## Out of Scope
```

Update state to `phase: tech-project-plan`.

## Step 6: Technical and Project Plan → `product/09-tech-project-plan.md`

Cover checkpoints 16 and 17:

```markdown
## Technical Plan

## Architecture Decision

## Project Plan

## Milestones

## Risks and Mitigations
```

If architecture selection is not settled, include the architecture decision here rather than routing to `/yishuship:arch-design`. Detailed architecture design can still go to `/yishuship:arch-design` after selection.

Update state to `phase: handoff`.

## Step 7: Engineering Handoff → `delivery/design-spec.md`

Write `delivery/design-spec.md` as the product-to-engineering bridge.

Required sections:

```markdown
## Engineering Goal

## Product Context

## Requirements

## Acceptance Criteria

## Constraints

## Source Artifacts
```

For compatibility, also write or update `plan/spec.md` with the same engineering-facing acceptance criteria when the next phase is `/yishuship:design` or `/yishuship:auto`.

Update state to `phase: complete` when handoff is ready.

## Step 8: Optional Growth Loop

Only run when the user asks for operation, data analysis, iteration, or learning.

Write:

```text
growth/01-ops-plan.md
growth/02-data-analysis.md
growth/03-iteration-plan.md
growth/04-learning.md
```

Growth output becomes the input to the next lifecycle iteration.
```

- [ ] **Step 2: Verify `pm-intake` references shared protocol and V2 layout**

Run:

```bash
cd /Users/mahaoxuan/Developer/yishuship
rg -n "product-lifecycle-21|product/00-product-type|lifecycle-checklist|delivery/design-spec" skills/pm-intake/SKILL.md
```

Expected: all four concepts are present.

- [ ] **Step 3: Check no old command pollution was introduced**

Run:

```bash
cd /Users/mahaoxuan/Developer/yishuship
rg -n "yishuship" skills/pm-intake/SKILL.md
```

Expected: no matches.

---

### Task 3: Add scorer regression tests first

**Files:**
- Create: `benchmarks/test_pm_scorer_lifecycle.py`
- Modify later: `benchmarks/pm_scorer.py`

- [ ] **Step 1: Write failing lifecycle scorer tests**

Create `benchmarks/test_pm_scorer_lifecycle.py`:

```python
from __future__ import annotations

import unittest

from pm_scorer import (
    CHECKPOINTS,
    CHECKPOINT_DEFINITIONS,
    QUALITY_DIMENSIONS,
    score_full_pipeline,
    score_lifecycle_artifact,
    score_lifecycle_pipeline,
    score_stage,
)


def rich_artifact(checkpoint: str) -> str:
    label = CHECKPOINT_DEFINITIONS[checkpoint]["label"]
    return f"""
# {label}

## Context
This section covers {label} for a real yishuship product task.
Evidence: https://example.com/research/{checkpoint}
User feedback sample: N=12, 7 repeated the same problem.
Competitor comparison: Existing tool A solves part of the workflow but misses the core scenario.

## Decision
Owner: PM
Action: convert this checkpoint into the next product or engineering artifact.
Acceptance criteria:
- Given the artifact exists, When engineering reads it, Then they can identify scope, constraints, and next steps.
- Risk: unclear ownership. Mitigation: assign one owner and one review gate.
"""


class LifecycleScorerTests(unittest.TestCase):
    def test_lifecycle_contract_stays_189_points(self) -> None:
        self.assertEqual(len(CHECKPOINTS), 21)
        self.assertEqual(QUALITY_DIMENSIONS, ("presence", "evidence", "actionability"))

        outputs = {checkpoint: rich_artifact(checkpoint) for checkpoint in CHECKPOINTS}
        result = score_lifecycle_pipeline(outputs)

        self.assertEqual(result["max"], 189)
        self.assertTrue(result["all_pass"])
        self.assertEqual(set(result["checkpoints"].keys()), set(CHECKPOINTS))

    def test_each_checkpoint_scores_three_quality_dimensions(self) -> None:
        result = score_lifecycle_artifact("prd", rich_artifact("prd"))

        self.assertEqual(result["max"], 9)
        self.assertEqual(result["pass_threshold"], 6)
        self.assertTrue(result["passOrFail"])
        self.assertEqual(set(result["details"].keys()), {"presence", "evidence", "actionability"})

    def test_missing_checkpoint_fails_without_reducing_total_max(self) -> None:
        outputs = {checkpoint: rich_artifact(checkpoint) for checkpoint in CHECKPOINTS if checkpoint != "permission"}
        result = score_lifecycle_pipeline(outputs)

        self.assertEqual(result["max"], 189)
        self.assertFalse(result["all_pass"])
        self.assertEqual(result["checkpoints"]["permission"]["total"], 0)
        self.assertFalse(result["checkpoints"]["permission"]["passOrFail"])

    def test_legacy_stage_api_still_works(self) -> None:
        stage_result = score_stage("discover", rich_artifact("scenario_research"))
        self.assertGreater(stage_result["max"], 0)
        self.assertIn("details", stage_result)

        pipeline_result = score_full_pipeline({"discover": rich_artifact("scenario_research")})
        self.assertGreater(pipeline_result["max"], 0)
        self.assertIn("stages", pipeline_result)

    def test_full_pipeline_accepts_lifecycle_outputs(self) -> None:
        outputs = {checkpoint: rich_artifact(checkpoint) for checkpoint in CHECKPOINTS}
        result = score_full_pipeline(outputs)

        self.assertEqual(result["max"], 189)
        self.assertIn("checkpoints", result)
        self.assertTrue(result["all_pass"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail against current scorer**

Run:

```bash
cd /Users/mahaoxuan/Developer/yishuship/benchmarks
python -m unittest test_pm_scorer_lifecycle.py -v
```

Expected: FAIL because `CHECKPOINTS`, `CHECKPOINT_DEFINITIONS`, `QUALITY_DIMENSIONS`, `score_lifecycle_artifact`, and `score_lifecycle_pipeline` are not defined yet.

---

### Task 4: Implement lifecycle scoring in `pm_scorer.py`

**Files:**
- Modify: `benchmarks/pm_scorer.py`
- Test: `benchmarks/test_pm_scorer_lifecycle.py`

- [ ] **Step 1: Replace `benchmarks/pm_scorer.py` with the V2 scorer**

Use a compact deterministic implementation that preserves public APIs:

```python
"""yishuship PM scorer — deterministic lifecycle scoring for SkillOpt and manual QA.

V2 scoring model:
21 product checkpoints × 3 quality dimensions × 3 points = 189.
"""
from __future__ import annotations

import re
from typing import Callable

QUALITY_DIMENSIONS = ("presence", "evidence", "actionability")

CHECKPOINT_DEFINITIONS: dict[str, dict[str, object]] = {
    "product_type": {"label": "产品类型判断", "keywords": ["产品类型", "product_type", "C", "B", "hybrid", "skip_rules"]},
    "brd": {"label": "BRD", "keywords": ["BRD", "为什么值得做", "商业价值", "值得做", "不做的代价"]},
    "mrd": {"label": "MRD", "keywords": ["MRD", "市场", "竞品", "竞争", "切换", "目标用户"]},
    "scenario_research": {"label": "业务 / 场景调研", "keywords": ["场景", "业务", "调研", "使用场景", "scenario"]},
    "current_state": {"label": "现状梳理", "keywords": ["现状", "当前", "现在", "已有方案", "替代方案", "current"]},
    "problem_summary": {"label": "问题总结", "keywords": ["问题", "痛点", "严重", "频率", "阻塞", "problem"]},
    "solution_idea": {"label": "解决思路", "keywords": ["解决思路", "方案思路", "solution", "假设", "路径"]},
    "product_solution": {"label": "产品方案", "keywords": ["产品方案", "产品形态", "范围", "功能", "solution"]},
    "product_blueprint": {"label": "产品定位 / 核心流程 / 演进蓝图", "keywords": ["定位", "核心流程", "蓝图", "roadmap", "演进"]},
    "data_model": {"label": "业务数据建模", "keywords": ["数据模型", "对象", "字段", "关系", "data model"]},
    "flow_role": {"label": "流程和角色", "keywords": ["流程", "角色", "handoff", "协作", "workflow"]},
    "interface_design": {"label": "界面设计", "keywords": ["界面", "页面", "screen", "状态", "交互"]},
    "report_design": {"label": "报表设计", "keywords": ["报表", "报告", "看板", "dashboard", "决策"]},
    "tracking": {"label": "数据埋点", "keywords": ["埋点", "事件", "指标", "tracking", "analytics"]},
    "permission": {"label": "权限管理", "keywords": ["权限", "角色", "访问", "permission", "risk"]},
    "prd": {"label": "PRD", "keywords": ["PRD", "需求", "验收", "acceptance", "Given"]},
    "technical_plan": {"label": "技术方案", "keywords": ["技术方案", "架构", "接口", "API", "technical"]},
    "project_management": {"label": "项目管理", "keywords": ["项目计划", "里程碑", "owner", "风险", "milestone"]},
    "delivery": {"label": "研发 / 测试 / 上线", "keywords": ["研发", "测试", "上线", "E2E", "QA", "release"]},
    "operations": {"label": "运营管理", "keywords": ["运营", "发布后", "告警", "监控", "operation"]},
    "iteration_analytics": {"label": "迭代优化 / 数据分析", "keywords": ["迭代", "数据分析", "复盘", "learning", "next iteration"]},
}

CHECKPOINTS: tuple[str, ...] = tuple(CHECKPOINT_DEFINITIONS.keys())

LEGACY_STAGE_CHECKPOINTS: dict[str, tuple[str, ...]] = {
    "discover": ("brd", "mrd", "scenario_research", "current_state", "problem_summary"),
    "arch-decision": ("product_type", "technical_plan"),
    "define": ("solution_idea", "product_solution", "product_blueprint", "tracking"),
    "design": ("data_model", "flow_role", "interface_design", "report_design", "permission", "prd", "technical_plan", "project_management"),
    "validate": ("problem_summary", "solution_idea", "prd"),
    "build": ("delivery",),
    "release": ("delivery", "operations"),
    "observe": ("operations", "iteration_analytics"),
    "learn": ("iteration_analytics",),
}

EVIDENCE_PATTERNS = [
    r"https?://",
    r"来源[:：]",
    r"证据[:：]",
    r"用户.*反馈",
    r"N\s*=\s*\d+",
    r"\d+%",
    r"\d+\s*(人|次|天|周|月)",
    r"竞品|竞争|对比|调研|数据|样本|案例",
]

ACTIONABILITY_PATTERNS = [
    r"Owner|负责人|责任人",
    r"下一步|行动|执行|交付|里程碑",
    r"验收|acceptance|Given.*When.*Then",
    r"风险|缓解|mitigation|Plan\s*B",
    r"必须|应该|需要|shall|must",
]

STRUCTURE_PATTERNS = [r"^#", r"^-\s+", r"^\d+\.", r"^\|.*\|", r"```"]


def _count_pattern(text: str, pattern: str) -> int:
    return len(re.findall(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL))


def _has_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL) for pattern in patterns)


def _clamp_score(value: int | float) -> float:
    return float(max(0, min(3, int(value))))


def _keyword_patterns(checkpoint: str) -> list[str]:
    definition = CHECKPOINT_DEFINITIONS[checkpoint]
    return [re.escape(str(keyword)) for keyword in definition["keywords"]]


def score_presence(checkpoint: str, text: str) -> float:
    """0=absent, 1=mentioned, 2=structured, 3=structured and substantial."""
    stripped = text.strip()
    if not stripped:
        return 0.0

    has_keyword = _has_any(stripped, _keyword_patterns(checkpoint))
    has_structure = _has_any(stripped, STRUCTURE_PATTERNS)
    has_substance = len(stripped) >= 240

    score = 0
    if has_keyword:
        score += 1
    if has_structure:
        score += 1
    if has_substance:
        score += 1
    return _clamp_score(score)


def score_evidence(checkpoint: str, text: str) -> float:
    """0=no support, 1=context only, 2=one evidence class, 3=multiple evidence classes."""
    stripped = text.strip()
    if not stripped:
        return 0.0

    hits = sum(1 for pattern in EVIDENCE_PATTERNS if re.search(pattern, stripped, re.IGNORECASE | re.DOTALL))
    if hits >= 3:
        return 3.0
    if hits >= 1:
        return 2.0
    if re.search(r"因为|所以|基于|context|背景", stripped, re.IGNORECASE):
        return 1.0
    return 0.0


def score_actionability(checkpoint: str, text: str) -> float:
    """0=not actionable, 1=intent, 2=action path, 3=owner/criteria/risk ready."""
    stripped = text.strip()
    if not stripped:
        return 0.0

    hits = sum(1 for pattern in ACTIONABILITY_PATTERNS if re.search(pattern, stripped, re.IGNORECASE | re.DOTALL))
    if hits >= 3:
        return 3.0
    if hits >= 2:
        return 2.0
    if hits >= 1:
        return 1.0
    return 0.0


def score_lifecycle_artifact(checkpoint: str, text: str) -> dict:
    """Score one lifecycle checkpoint on presence, evidence, and actionability."""
    if checkpoint not in CHECKPOINT_DEFINITIONS:
        raise KeyError(f"Unknown lifecycle checkpoint: {checkpoint}")

    details = {
        "presence": score_presence(checkpoint, text),
        "evidence": score_evidence(checkpoint, text),
        "actionability": score_actionability(checkpoint, text),
    }
    total = sum(details.values())
    return {
        "total": total,
        "max": 9,
        "pass_threshold": 6,
        "passOrFail": total >= 6,
        "details": details,
    }


def score_lifecycle_pipeline(outputs: dict[str, str]) -> dict:
    """Score all 21 lifecycle checkpoints. Missing checkpoints score zero."""
    results = {}
    total = 0.0
    all_pass = True

    for checkpoint in CHECKPOINTS:
        if checkpoint in outputs:
            result = score_lifecycle_artifact(checkpoint, outputs[checkpoint])
        else:
            result = {
                "total": 0.0,
                "max": 9,
                "pass_threshold": 6,
                "passOrFail": False,
                "details": {dimension: 0.0 for dimension in QUALITY_DIMENSIONS},
            }
        results[checkpoint] = result
        total += result["total"]
        all_pass = all_pass and result["passOrFail"]

    return {
        "checkpoints": results,
        "total": total,
        "max": len(CHECKPOINTS) * len(QUALITY_DIMENSIONS) * 3,
        "all_pass": all_pass,
    }


def _combine_stage_output(stage: str, output: str) -> dict[str, str]:
    checkpoints = LEGACY_STAGE_CHECKPOINTS[stage]
    return {checkpoint: output for checkpoint in checkpoints}


def score_stage(stage: str, output: str) -> dict:
    """Score one legacy stage or one lifecycle checkpoint."""
    if stage in CHECKPOINT_DEFINITIONS:
        return score_lifecycle_artifact(stage, output)

    if stage not in LEGACY_STAGE_CHECKPOINTS:
        raise KeyError(f"Unknown PM stage: {stage}")

    stage_outputs = _combine_stage_output(stage, output)
    checkpoint_results = {checkpoint: score_lifecycle_artifact(checkpoint, text) for checkpoint, text in stage_outputs.items()}
    total = sum(result["total"] for result in checkpoint_results.values())
    max_score = len(checkpoint_results) * 9
    pass_threshold = max(1, len(checkpoint_results) * 6)

    return {
        "total": total,
        "max": max_score,
        "pass_threshold": pass_threshold,
        "passOrFail": total >= pass_threshold,
        "details": checkpoint_results,
    }


def _looks_like_lifecycle_outputs(outputs: dict[str, str]) -> bool:
    return bool(outputs) and all(key in CHECKPOINT_DEFINITIONS for key in outputs.keys())


def score_full_pipeline(outputs: dict[str, str]) -> dict:
    """Score lifecycle outputs or legacy stage outputs.

    Lifecycle input shape:
        {"product_type": "...", "brd": "...", ...}

    Legacy input shape:
        {"discover": "...", "define": "...", ...}
    """
    if _looks_like_lifecycle_outputs(outputs):
        return score_lifecycle_pipeline(outputs)

    results = {}
    total = 0.0
    max_total = 0.0
    all_pass = True

    for stage, checkpoints in LEGACY_STAGE_CHECKPOINTS.items():
        if stage in outputs:
            result = score_stage(stage, outputs[stage])
        else:
            max_score = len(checkpoints) * 9
            result = {
                "total": 0.0,
                "max": max_score,
                "pass_threshold": max(1, len(checkpoints) * 6),
                "passOrFail": False,
                "details": {},
            }
        results[stage] = result
        total += result["total"]
        max_total += result["max"]
        all_pass = all_pass and result["passOrFail"]

    return {
        "stages": results,
        "total": total,
        "max": max_total,
        "all_pass": all_pass,
    }
```

- [ ] **Step 2: Run scorer tests**

Run:

```bash
cd /Users/mahaoxuan/Developer/yishuship/benchmarks
python -m unittest test_pm_scorer_lifecycle.py -v
```

Expected: PASS, five tests.

- [ ] **Step 3: Compile scorer**

Run:

```bash
cd /Users/mahaoxuan/Developer/yishuship
python -m py_compile benchmarks/pm_scorer.py benchmarks/test_pm_scorer_lifecycle.py
```

Expected: no output and exit code 0.

---

### Task 5: Fix routing and auto documentation

**Files:**
- Modify: `skills/use-yishuship/SKILL.md`
- Modify: `skills/auto/SKILL.md`

- [ ] **Step 1: Replace `/yishuship:*` with `/yishuship:*` in routing docs**

Run:

```bash
cd /Users/mahaoxuan/Developer/yishuship
python - <<'PY'
from pathlib import Path
path = Path('skills/use-yishuship/SKILL.md')
text = path.read_text()
path.write_text(text.replace('/yishuship:', '/yishuship:'))
PY
```

- [ ] **Step 2: Update `use-yishuship` routing language**

Edit `skills/use-yishuship/SKILL.md` so the first routing block says:

```text
新功能 / 产品方向 → /yishuship:pm-intake(product lifecycle) → /yishuship:design
Bug / 小修复      → /yishuship:review 或直接修
纯技术重构        → /yishuship:design (refactor scope)
运营 / 数据 / 复盘 → /yishuship:pm-intake Step 8 growth loop
不确定           → 问用户：这是新功能、修复、重构，还是增长复盘？
```

Add this section after the first routing block:

```markdown
## 产品类型先判定

当请求是新产品、新功能、商业化、增长、运营、B 端流程、C 端体验时，先判断产品类型：

- C：优先追问用户动机、留存、复用、分享、付费、流失、核心行为闭环。
- B：优先追问业务流程、角色、权限、数据对象、报表、风险控制、组织协作。
- hybrid：同时记录用户与购买者，明确哪些 checkpoint required，哪些 optional，哪些 N/A。

产品类型判断由 `/yishuship:pm-intake` 写入 `product/00-product-type.yaml`。
```

- [ ] **Step 3: Update auto skill flow**

Edit `skills/auto/SKILL.md` so the description and execution section state:

```markdown
Full staged workflow for explicit end-to-end production delivery:

```text
pm-intake(product lifecycle) → PM Gate → design → dev → e2e → review → qa → refactor → handoff
```

Growth Loop is an optional continuation after handoff, not a mandatory phase for every feature.
```

Keep the existing `auto-orchestrate.sh` invocation. Add this compatibility note:

```markdown
The underlying orchestrator still dispatches the engineering state machine. V2 product lifecycle artifacts are enforced by PM Gate and by the handoff generated from `/yishuship:pm-intake`.
```

- [ ] **Step 4: Verify command prefix cleanup**

Run:

```bash
cd /Users/mahaoxuan/Developer/yishuship
rg -n "yishuship" skills/use-yishuship/SKILL.md skills/auto/SKILL.md
```

Expected: no matches.

---

### Task 6: Upgrade PM gate scripts with V2 fallback

**Files:**
- Modify: `scripts/pm-gate.sh`
- Modify: `scripts/pm-verify.sh`

- [ ] **Step 1: Update `pm-gate.sh` artifact checks**

In `scripts/pm-gate.sh`, add helper functions above the design/dev rules:

```bash
has_v2_product_handoff() {
  [ -f "$TASK_DIR/product/00-product-type.yaml" ] && \
  [ -f "$TASK_DIR/product/01-strategy.md" ] && \
  [ -f "$TASK_DIR/product/03-problem-solution.md" ] && \
  [ -f "$TASK_DIR/product/08-prd.md" ] && \
  [ -f "$TASK_DIR/product/09-tech-project-plan.md" ]
}

has_legacy_discovery() {
  [ -f "$PM_DIR/01-discovery.md" ]
}

has_legacy_definition() {
  [ -f "$PM_DIR/02-definition.md" ]
}
```

Then replace the design rule body with:

```bash
if echo "$AGENT_PROMPT" | grep -q "yishuship:design\|yishuship:auto"; then
  if ! has_v2_product_handoff && ! has_legacy_discovery; then
    block "[yishuship PM gate] /yishuship:design 需要先完成产品生命周期入口。请运行 /yishuship:pm-intake，至少产出 product/00-product-type.yaml、product/01-strategy.md、product/03-problem-solution.md、product/08-prd.md、product/09-tech-project-plan.md。旧任务可用 pm/01-discovery.md 兼容通过。"
    exit 0
  fi
fi
```

Replace the dev rule body with:

```bash
if echo "$AGENT_PROMPT" | grep -q "yishuship:dev"; then
  if ! has_v2_product_handoff && ! has_legacy_definition; then
    block "[yishuship PM gate] /yishuship:dev 需要可执行产品交接。请先完成 /yishuship:pm-intake 的 PRD 和技术项目计划。旧任务可用 pm/02-definition.md 兼容通过。"
    exit 0
  fi
fi
```

- [ ] **Step 2: Update `pm-verify.sh` phase cases**

In `scripts/pm-verify.sh`, update the missing-file case to understand V2 phases:

```bash
case "$PM_PHASE" in
  product-type)
    [ ! -f "$TASK_DIR/product/00-product-type.yaml" ] && MISSING="$MISSING\n- product/00-product-type.yaml（产品类型判断）"
    ;;
  strategy)
    [ ! -f "$TASK_DIR/product/00-product-type.yaml" ] && MISSING="$MISSING\n- product/00-product-type.yaml（产品类型判断）"
    [ ! -f "$TASK_DIR/product/01-strategy.md" ] && MISSING="$MISSING\n- product/01-strategy.md（战略与市场）"
    ;;
  research)
    [ ! -f "$TASK_DIR/product/02-research.md" ] && MISSING="$MISSING\n- product/02-research.md（业务 / 场景调研）"
    ;;
  problem-solution)
    [ ! -f "$TASK_DIR/product/03-problem-solution.md" ] && MISSING="$MISSING\n- product/03-problem-solution.md（问题与方案）"
    [ ! -f "$TASK_DIR/product/04-product-blueprint.md" ] && MISSING="$MISSING\n- product/04-product-blueprint.md（产品蓝图）"
    ;;
  product-spec)
    [ ! -f "$TASK_DIR/product/05-model-flow-role.md" ] && MISSING="$MISSING\n- product/05-model-flow-role.md（模型 / 流程 / 角色）"
    [ ! -f "$TASK_DIR/product/06-experience-spec.md" ] && MISSING="$MISSING\n- product/06-experience-spec.md（体验规格）"
    [ ! -f "$TASK_DIR/product/07-data-permission-analytics.md" ] && MISSING="$MISSING\n- product/07-data-permission-analytics.md（数据 / 权限 / 分析）"
    [ ! -f "$TASK_DIR/product/08-prd.md" ] && MISSING="$MISSING\n- product/08-prd.md（PRD）"
    ;;
  tech-project-plan)
    [ ! -f "$TASK_DIR/product/09-tech-project-plan.md" ] && MISSING="$MISSING\n- product/09-tech-project-plan.md（技术与项目计划）"
    ;;
  handoff)
    [ ! -f "$TASK_DIR/delivery/design-spec.md" ] && [ ! -f "$TASK_DIR/plan/spec.md" ] && MISSING="$MISSING\n- delivery/design-spec.md 或 plan/spec.md（工程交接规格）"
    ;;
  discover|define|design|validate)
    # Keep the existing legacy cases for old tasks.
    ;;
  complete)
    exit 0
    ;;
  *)
    exit 0
    ;;
esac
```

Preserve the existing legacy cases for `discover`, `define`, `design`, and `validate` below or above the new cases; do not remove old compatibility.

- [ ] **Step 3: Syntax-check shell scripts**

Run:

```bash
cd /Users/mahaoxuan/Developer/yishuship
bash -n scripts/pm-gate.sh
bash -n scripts/pm-verify.sh
```

Expected: no output and exit code 0.

---

### Task 7: Update docs and metadata

**Files:**
- Modify: `README.md`
- Modify: `docs/SKILLOPT_TRAINING.md`
- Modify: `DEVLOG.md`
- Modify: `AGENTS.md`
- Optionally modify: `.claude-plugin/plugin.json`
- Optionally modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Update README positioning**

In `README.md`, replace the core architecture block with:

```text
PM 生命周期层（yishuship V2）
  Idea → Product Type → Strategy → Research → Definition → Specification
                                      ↓
工程层（原版 Ship）
  对抗式设计 → 实现 → E2E → Review → QA → Refactor → Handoff
                                      ↓
Growth Loop（可选）
  运营 → 数据分析 → 迭代计划 → Learning → 下一轮 Idea
```

Update the PM Intake row to say:

```markdown
| PM Intake | `/yishuship:pm-intake` | **V2**：产品生命周期入口，21 checkpoint，不是 21 强制阶段 |
```

Update scoring language to:

```markdown
| 评分框架 | 无 | 21 检查点 × 3 质量维度 × 3 分 = 189 分 |
```

- [ ] **Step 2: Update SkillOpt training doc score model**

In `docs/SKILLOPT_TRAINING.md`, replace the score drift paragraph with:

```markdown
## V2 Scoring Model

V2 keeps the 189-point ceiling but changes the meaning:

```text
21 product lifecycle checkpoints × 3 quality dimensions × 3 points = 189
```

The three quality dimensions are:

- `presence`: the checkpoint exists and contains concrete content.
- `evidence`: the checkpoint is supported by user, business, data, competitor, case, or local-context evidence.
- `actionability`: the checkpoint can be handed to design, engineering, QA, operations, or the next iteration.

`pm_scorer.py` preserves the legacy `score_stage()` and `score_full_pipeline()` functions for SkillOpt compatibility, while adding lifecycle-native scoring.
```

- [ ] **Step 3: Add DEVLOG entry**

Add a new top entry to `DEVLOG.md`:

```markdown
## 2026-06-29 — yishuship V2 生命周期协议

- 将 yishuship 从“PM 前置 + 工程交付”升级为“产品全生命周期工作流”。
- 保留 `/yishuship:pm-intake` 命令名，内部升级为 Product Lifecycle Intake。
- 新增 21 个产品 checkpoint 的共享协议，阶段负责推进，checkpoint 负责不遗漏。
- 评分心智统一为 `21 检查点 × 3 质量维度 × 3 分 = 189 分`。
- `/yishuship:auto` 同步理解 product lifecycle，growth loop 作为 handoff 后可选 continuation。
- PM gate 优先检查 V2 `product/*` 产物，并保留旧 `pm/*` 兼容。
```

- [ ] **Step 4: Update AGENTS repository map**

In `AGENTS.md`, update the `pm-intake/` line to:

```text
  pm-intake/        产品生命周期入口：类型判断→战略→调研→规格→工程交接
```

Add under `.shared/`:

```text
  .shared/          共享参考（product-lifecycle-21, runtime-resolution, report-card, startup, cleanup）
```

- [ ] **Step 5: Update plugin metadata if old wording is present**

Run:

```bash
cd /Users/mahaoxuan/Developer/yishuship
rg -n "PM 层|8 阶段|63 维|189|pm-intake" .claude-plugin README.md docs DEVLOG.md AGENTS.md
```

If `.claude-plugin/*.json` still says only “PM 层 + 工程执行”, update descriptions to mention “产品生命周期”. Keep JSON valid.

---

### Task 8: Final validation

**Files:**
- Validate all changed files.

- [ ] **Step 1: Confirm no polluted command prefix remains in docs and skills**

Run:

```bash
cd /Users/mahaoxuan/Developer/yishuship
rg -n "yishuship" skills scripts README.md docs AGENTS.md .claude-plugin || true
```

Expected: no matches. If matches remain in intentional historical examples, change them unless they are in generated cache outside this repo.

- [ ] **Step 2: Run scorer tests**

Run:

```bash
cd /Users/mahaoxuan/Developer/yishuship/benchmarks
python -m unittest test_pm_scorer_lifecycle.py -v
```

Expected: PASS.

- [ ] **Step 3: Compile Python**

Run:

```bash
cd /Users/mahaoxuan/Developer/yishuship
python -m py_compile benchmarks/pm_scorer.py benchmarks/test_pm_scorer_lifecycle.py
```

Expected: no output and exit code 0.

- [ ] **Step 4: Syntax-check shell scripts**

Run:

```bash
cd /Users/mahaoxuan/Developer/yishuship
bash -n scripts/pm-gate.sh
bash -n scripts/pm-verify.sh
```

Expected: no output and exit code 0.

- [ ] **Step 5: Inspect changed files**

Run:

```bash
cd /Users/mahaoxuan/Developer/yishuship
git status --short
git diff --stat
git diff -- skills/.shared/product-lifecycle-21.md skills/pm-intake/SKILL.md benchmarks/pm_scorer.py benchmarks/test_pm_scorer_lifecycle.py skills/use-yishuship/SKILL.md skills/auto/SKILL.md scripts/pm-gate.sh scripts/pm-verify.sh README.md docs/SKILLOPT_TRAINING.md DEVLOG.md AGENTS.md .claude-plugin/plugin.json .claude-plugin/marketplace.json
```

Expected:

- Only planned files changed, plus the pre-existing `benchmarks/__pycache__/pm_scorer.cpython-313.pyc` dirty file.
- No unrelated refactor.
- No deleted compatibility paths.

- [ ] **Step 6: Report result**

Report in Chinese:

```text
已完成 yishuship V2 生命周期协议改造。

验证：
- 命令前缀污染：通过 / 未通过
- Python scorer tests：通过 / 未通过
- Python compile：通过 / 未通过
- Bash syntax：通过 / 未通过

主要文件：
- skills/.shared/product-lifecycle-21.md
- skills/pm-intake/SKILL.md
- benchmarks/pm_scorer.py
- skills/use-yishuship/SKILL.md
- scripts/pm-gate.sh

剩余风险：
- growth loop 仍为可选 continuation，未接入 auto 状态机强制阶段。
- 旧 `.ship/tasks/*/pm/` 通过 fallback 兼容，后续可在实际任务中逐步迁移到 `product/`。
```
