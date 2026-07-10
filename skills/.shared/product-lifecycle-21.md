# yishuship V2 Product Lifecycle Protocol

This shared reference is the canonical source for yishuship's product lifecycle. Skills should link here instead of duplicating the full checklist.

## Core Principle

Do not turn 21 product processes into 21 mandatory phases. Use a small number of phases to move work forward, and use checkpoints to prevent product thinking from being skipped.

**Scope before volume:** challenge which requirements must exist (owner, keep/cut/defer) before expanding strategy, blueprint, and PRD. Specifying a feature that should have been cut is a product bug.

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
    00-product-type.json
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

`product/00-product-type.json` decides which checkpoints are required, optional, or not applicable.

```json
{
  "product_type": "C | B | hybrid",
  "primary_user": "",
  "buyer_or_user": "",
  "core_scene": "",
  "workflow_weight": {
    "strategy": "required",
    "research": "required",
    "data_model": "required | optional",
    "permission": "required | optional",
    "report": "required | optional",
    "analytics": "required"
  },
  "skip_rules": [
    {
      "checkpoint": "",
      "reason": ""
    }
  ]
}
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
| 0 | product_type | C / B / hybrid and skip rules | `product/00-product-type.json` |
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

- `product/00-product-type.json`
- `product/01-strategy.md`
- `product/03-problem-solution.md`
- `product/08-prd.md`
- `product/09-tech-project-plan.md`

Existing legacy tasks with `pm/01-discovery.md`, `pm/02-definition.md`, `pm/03-design.md`, and `pm/04-validation.md` remain valid through fallback checks.