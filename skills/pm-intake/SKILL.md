---
name: pm-intake
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

Read `../.shared/product-lifecycle-21.md` and
`../.shared/matt-pocock-standard.md` before producing artifacts. Do not
duplicate those protocols in this skill; use them as shared sources of truth.

Also read the relevant upstream Matt skills before executing their lane:

- Always read `../../vendor/mattpocock-skills/skills/engineering/grill-with-docs/SKILL.md`.
- Always read `../../vendor/mattpocock-skills/skills/productivity/grilling/SKILL.md`.
- Always read `../../vendor/mattpocock-skills/skills/engineering/domain-modeling/SKILL.md`.
- Read `../../vendor/mattpocock-skills/skills/engineering/to-spec/SKILL.md` before writing PRD/spec artifacts.
- Read `../../vendor/mattpocock-skills/skills/engineering/prototype/SKILL.md` when a product/design question needs a runnable answer.
- Read `../../vendor/mattpocock-skills/skills/engineering/research/SKILL.md` when product claims need primary-source investigation (official docs, APIs, first-party code).

## Hard Rules

- Keep `/yishuship:pm-intake` as the command name.
- Do not send an idea directly to code.
- **Challenge scope before thickening docs.** Before strategy/PRD, write
  `product/00b-scope-challenge.md` (or the Scope Challenge section in strategy):
  which requirements must exist, who owns each, what is deleted or deferred, and
  why. Do not optimize or specify features that fail this cut.
- Product type must be decided before strategy, research, PRD, or technical planning.
- Misalignment is a product bug. If intent, domain language, or a decision branch is unresolved, ask the next blocking question before writing engineering handoff.
- Treat the 21 items as checkpoints, not as 21 mandatory phases.
- Maintain shared language: update or create `CONTEXT.md` when a domain term is resolved; record hard-to-reverse trade-offs in `docs/decisions/`.
- If a question cannot be settled in conversation, route through a throwaway prototype and preserve only the answer in product artifacts.
- Mark each checkpoint as `required`, `optional`, or `N/A` with a reason.
- Growth artifacts are optional unless the user explicitly asks for launch, operation, data review, or next-iteration work.
- If the task is a tiny bug fix with no product decision, route to `/yishuship:review` or `/yishuship:dev` instead of forcing lifecycle intake.
- **Matt upstream is mandatory, not decorative.** Before DONE, write
  `control/matt-upstream.md` listing each required Matt `SKILL.md` path you
  actually opened this run (at least grill-with-docs, grilling, domain-modeling,
  and to-spec when producing PRD/spec). Empty list = incomplete phase.
- **Checkpoints are a spiral map.** pre_cycle / in_cycle / post_cycle timing is
  defined in `product-lifecycle-21.md`. Do not pretend all 21 are finished before
  code; do not skip post_cycle learning when the user asks for a full lifecycle.
- **Peer cross-review of product inputs and outputs** (full scope): after draft
  handoff artifacts exist, dispatch an independent peer to review scope + PRD +
  design-spec against the checklist in `product-lifecycle-21.md`. Write findings
  to `control/peer-review.md` and resolve them before DONE. If peer unavailable,
  self-second-pass with `WARNING: peer self-generated`.

## Step 0: Initialize

Create or reuse a task directory and state files.

If the caller provides `task_id` and `task_dir` (for example from `/yishuship:auto`),
reuse those exact values and do not create a separate timestamp task. If no
task context is provided, initialize a new task:

```bash
TASK_ID="${TASK_ID:-$(date +%Y%m%d-%H%M%S)}"
TASK_DIR="${TASK_DIR:-.ship/tasks/$TASK_ID}"
mkdir -p "$TASK_DIR"/{input,product,delivery,growth,control,plan,e2e,qa}
cat > ".ship/pm-state.yaml" << EOF
phase: product-type
task_id: $TASK_ID
created: $(date -Iseconds)
workflow: product-lifecycle-v2
EOF
cat > "$TASK_DIR/control/run_state.yaml" << EOF
task_id: $TASK_ID
active: true
current_phase: product-type
status: running
workflow: product-lifecycle-v2
updated_at: "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
EOF
```

Write the user's original idea to `$TASK_DIR/input/idea.md` unless it already
exists. Preserve `$TASK_DIR/input/requirement.md` when it was created by
`/yishuship:auto`.

Create TodoWrite items:

1. Product type
2. Scope challenge (keep / cut / defer + owners)
3. Alignment and shared language
4. Strategy and market
5. Research and current state
6. Problem and solution
7. Product specification and test seams
8. Technical and project plan
9. Engineering handoff
10. Peer cross-review of handoff (inputs + outputs)
11. Optional growth loop

## Scope Challenge Gate (before thick strategy/PRD)

After product type (or in parallel with it when type is obvious), write
`$TASK_DIR/product/00b-scope-challenge.md`:

```markdown
## Candidate requirements
| Requirement | Owner (who asked) | Keep / Cut / Defer | Reason |

## Deleted or deferred
- ...

## Must-ship this cycle
- ...

## Explicit non-goals
- ...
```

Rules:

- Every "must" line has an owner (person or role), not "the business" or "everyone".
- Prefer cutting before specifying. If nothing was cut or deferred, say why the
  scope is already minimal.
- Strategy, blueprint, and PRD must not reintroduce cut items without updating
  this file.

## Alignment and Shared Language Gate

Before Step 2 is complete, apply the vendored `grill-with-docs` /
`domain-modeling` discipline:

- Ask one decision question at a time when the next artifact depends on the answer.
- Challenge vague or overloaded terms and propose canonical vocabulary.
- Stress-test product relationships with concrete edge scenarios.
- Cross-check local code/docs when user claims how an existing system works.
- Update `CONTEXT.md` inline when a term is settled.
- Create a decision record only when the trade-off is hard to reverse,
  surprising without context, and chosen from real alternatives.

## Step 1: Product Type → `product/00-product-type.json`

Classify the product as `C`, `B`, or `hybrid`.

Ask only what is needed to classify. Prefer one question at a time.

Write:

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

Also write `$TASK_DIR/control/lifecycle-checklist.yaml` with all 21 checkpoints and their `required`, `optional`, or `N/A` status.

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

`08-prd.md` covers the executable PRD. **These three sections are required**
(auto and standalone DONE both check headings):

```markdown
## Product Requirements

## Acceptance Criteria

## Success Metrics
<!-- North-star or task-complete metrics; how we know this shipped well -->

## Assumptions
<!-- What we are guessing; how each will be validated or falsified -->

## Kill Criteria
<!-- Stop / do-not-continue signals if the idea is wrong -->

## Testing Seams

## Vertical Slice Candidates

## Edge Cases

## Out of Scope
```

Testing seams follow Matt's `to-spec` standard: prefer the highest existing seam
that verifies user-visible behavior; propose new seams only when existing ones
cannot catch the important behavior.

**Scope modes (auto `scope_mode`):**

| Mode | When | Required product files |
|------|------|------------------------|
| `lite` | fix/bug/patch/small… | minimum handoff: 00, 00b, 01, 03, 08, 09 + design-spec + plan/spec + matt-upstream + checklist (peer-review optional) |
| `full` / `refactor` | default new feature / product | full suite: also 02, 04, 05, 06, 07 + **control/peer-review.md** (required; auto + pm-gate enforce) |

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

If the work is multi-session, include tracer-bullet vertical slices in the
engineering handoff: each slice must be independently demoable or verifiable
and must not be a horizontal layer-only task.

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

## Step 7b: Peer cross-review (full / refactor; optional on lite)

Before marking complete on **full** or **refactor** scope (auto `scope_mode`, or
standalone handoff that includes `02-research` / full suite files):

1. Dispatch an independent peer (or self-second-pass with
   `WARNING: peer self-generated` if no peer runtime).
2. Peer reviews product **inputs** (idea, claims, sources) and **outputs**
   (scope, PRD, design-spec, plan/spec) against the checklist in
   `product-lifecycle-21.md`.
3. Write `$TASK_DIR/control/peer-review.md` with findings (or explicit clean
   pass) **and** host disposition (`accept` / `reject+reason` / resolved).

Auto `complete pm_intake` and `pm-gate.sh` both require this file on full suite.
Lite may omit it, or record a one-line waiver.

Update state to `phase: complete` when handoff (and peer-review if required) is ready.

## Completion Gate

Done means the V2 product handoff is complete in the same `$TASK_DIR`: all
required checkpoints are marked in `control/lifecycle-checklist.yaml` (with
when: pre_cycle/in_cycle/post_cycle when known), required product files exist
under `product/` (including `00b-scope-challenge.md` unless N/A with reason),
`control/matt-upstream.md` lists Matt paths actually opened,
`control/peer-review.md` exists for full scope (or lite waiver with reason),
`delivery/design-spec.md` bridges product to engineering, and `plan/spec.md`
contains engineering-facing acceptance criteria. If any required checkpoint is
unknown, mark the phase `BLOCKED` rather than inventing certainty.

## [PM Intake] Report Card

| Field | Value |
|-------|-------|
| Status | <DONE / BLOCKED> |
| Product type | <C / B / hybrid> |
| Scope challenge | <path or N/A + reason> |
| Matt upstream read | <paths from control/matt-upstream.md> |
| Peer review | <path or lite-waived> |
| Required checkpoints complete | <N>/<N> |
| Optional checkpoints skipped | <checkpoint + reason> |
| Main evidence | <sources, examples, or assumptions> |
| Handoff artifacts | `$TASK_DIR/delivery/design-spec.md`, `$TASK_DIR/plan/spec.md` |

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
