# yishuship V2 Product Lifecycle Protocol

This shared reference is the canonical source for yishuship's product lifecycle. Skills should link here instead of duplicating the full checklist.

## Core Principle

Do not turn 21 product processes into 21 mandatory phases. Use a small number of phases to move work forward, and use checkpoints to prevent product thinking from being skipped.

**Scope before volume:** challenge which requirements must exist (owner, keep/cut/defer) before expanding strategy, blueprint, and PRD. Specifying a feature that should have been cut is a product bug.

**Spiral, not waterfall:** the 21 checkpoints are a **lifecycle map**, not 21 steps that must finish before code. One delivery pass is one arc of a spiral. Later arcs re-open only the checkpoints that new evidence touches.

```text
Idea
→ Product Type
→ Strategy Gate
→ Research Gate
→ Product Definition Gate
→ Product Specification Gate
→ Engineering Delivery
→ Release
→ Growth Loop  ──feeds next idea / scope change──┐
      ▲                                           │
      └────────── next cycle (partial re-open) ───┘
```

## Standard Task Layout

```text
.ship/tasks/<task_id>/
  input/
    idea.md

  product/
    00-product-type.json
    00b-scope-challenge.md
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
    matt-upstream.md
    peer-review.md
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

## Checkpoint timing (when in the spiral)

Each checkpoint has a **when** status, not only required/optional/N/A:

| When | Meaning |
|------|---------|
| `pre_cycle` | Enough answer needed before engineering spends real build effort this cycle |
| `in_cycle` | Deepened or finished during design/dev/verify this cycle |
| `post_cycle` | Only meaningful after ship or with real usage/ops data |
| `continuous` | May re-open any cycle when evidence changes |

Default placement (override with reason in `lifecycle-checklist.yaml`):

| # | Checkpoint | Default when |
|---|------------|--------------|
| 0 | product_type | `pre_cycle` |
| 0b | scope challenge (keep/cut/defer) | `pre_cycle` |
| 1–2 | brd / mrd | `pre_cycle` (depth scales with lite/full) |
| 3–4 | research / current_state | `pre_cycle` on full; thin or later on lite |
| 5–8 | problem / solution / blueprint | `pre_cycle` for boundaries; may refine `in_cycle` |
| 9–14 | model / flow / UI / report / tracking / permission | often `pre_cycle` light + `in_cycle` deep; lite may defer some |
| 15 | prd (+ metrics, assumptions, kill criteria) | `pre_cycle` required for handoff |
| 16–17 | technical + project plan | `pre_cycle` enough to start; detail `in_cycle` |
| 18 | delivery evidence | `in_cycle` / end of cycle (e2e, qa, handoff) |
| 19 | operations | `post_cycle` (or pre-launch plan if launching) |
| 20 | iteration analytics | `post_cycle` + **must be able to open next cycle** |

### One cycle vs the map

- **pm-intake** = this cycle's **pre_cycle** slice (lite minimum or full suite), not a promise that all 21 are done forever.
- **design / dev / e2e / review / qa / handoff** = **in_cycle** execution and evidence (checkpoint 18 and in-cycle refinements).
- **growth / learn** = **post_cycle** (19–20). Output should name which checkpoints re-open next.

### Feedback links (expected loops)

```text
qa / e2e evidence  → may change assumptions, metrics, kill criteria (15)
metrics / users    → may change problem, scope, PRD (5–8, 15, 0b)
tech reality       → may change technical plan (16) and scope (0b)
ops incidents      → may change permissions, tracking, ops plan (13–14, 19)
learning (20)      → writes next input/idea.md or requirement.md and re-enters intake
```

Do not re-run all 21 from zero each time. Re-open **touched** checkpoints only, with a one-line reason.

## Multi-agent cross-review (inputs and outputs)

Product work must not be a single-agent monologue. Independent review of **inputs** and **outputs** is mandatory for non-trivial cycles (full scope; lite may use a lighter peer pass but cannot skip review of PRD/handoff).

### Principles (aligned with continuous discovery practice)

- Discovery and delivery are dual tracks: validate risk before and while building, not only after a giant PRD ([Paweł Huryn on Product Discovery](https://x.com/PawelHuryn/status/1756701712537059715) - five risks: value, usability, viability, feasibility, ethics; PM+design+engineering perspectives).
- Avoid "project disguised as product": no pure waterfall of requirements then feature factory without discovery or metrics ([red flags / better way](https://x.com/PawelHuryn/status/1725421757530522065)).
- Kill weak scope early with explicit criteria ([example kill-before-code framing](https://x.com/WasimShips/status/2075180804343316700)).
- Cross-functional challenge beats one role deciding alone.

### Required pattern in yishuship

| Artifact class | Producer | Reviewer (independent) | What is checked |
|----------------|----------|------------------------|-----------------|
| Scope challenge + strategy/problem | host pm-intake | peer agent | keep/cut honesty, owners, non-goals, weak evidence flags |
| PRD + design-spec + plan/spec | host pm-intake (or design) | peer agent | test seams, metrics, assumptions, kill criteria, actionability |
| design plan/spec | design host | design peer (already required) | code-grounded divergence |
| implementation | dev host | peer per story (already required) | spec compliance + quality |
| e2e / review / qa reports | phase host | optional second pass on full; required if verdict success with thin evidence | evidence vs claim |

Rules:

1. Reviewer must **not** be the same session that wrote the artifact when a peer is available (`runtime-resolution.md`).
2. Review covers **inputs** (idea, claims, data sources) and **outputs** (docs, specs, metrics).
3. Peer findings write to `control/peer-review.md` (or phase-local peer file). Host must respond: accept / reject+reason / change artifact.
4. `DONE` without peer response on full-scope pm-intake handoff is invalid when peer dispatch is available.
5. If peer is unavailable, self-produce a second pass and mark `WARNING: peer self-generated` (same bar as design).

### Minimum peer checklist for product handoff

- [ ] Scope: something was cut or deferred, or explicit why not
- [ ] Each must-ship has an owner
- [ ] Success metrics are measurable
- [ ] Assumptions are falsifiable
- [ ] Kill criteria are concrete
- [ ] Claims cite evidence or are labeled assumption
- [ ] Engineering can implement without guessing product intent

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

### Minimum handoff (`scope_mode: lite` or gate for design/dev)

Not a perfect 189 score. Must include:

- `product/00-product-type.json`
- `product/00b-scope-challenge.md`
- `product/01-strategy.md`
- `product/03-problem-solution.md`
- `product/08-prd.md` (with Success Metrics, Assumptions, Kill Criteria)
- `product/09-tech-project-plan.md`
- `control/matt-upstream.md`
- `control/lifecycle-checklist.yaml`
- `delivery/design-spec.md`
- `plan/spec.md`

### Full suite (`scope_mode: full` or `refactor` under auto)

Also require:

- `02-research.md`, `04-product-blueprint.md`
- `05-model-flow-role.md`, `06-experience-spec.md`, `07-data-permission-analytics.md`
- `control/peer-review.md` (peer findings + host disposition on product inputs/outputs)

`pm-gate.sh` and `auto-orchestrate.sh` validate the same sets: lite = minimum only;
full/refactor = minimum + full suite files + peer-review. Do not diverge these lists
without updating both scripts and this section together.

Existing legacy tasks with `pm/01-discovery.md`, `pm/02-definition.md`, `pm/03-design.md`, and `pm/04-validation.md` remain valid through fallback checks.
