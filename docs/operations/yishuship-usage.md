# yishuship Usage

## What yishuship Is

yishuship is a PM + engineering delivery workflow. It routes a request through
the lightest path that preserves quality.

Its default high-quality chain is:

```text
alignment / shared language
→ PRD with test seams
→ vertical slices
→ TDD implementation
→ two-axis review
→ handoff
```

Use yishuship when the work is more than a tiny local edit, or when the request
needs product judgment, architecture judgment, implementation, verification, or
release discipline.

## Main Entry

Use the router first when the correct phase is not obvious:

```text
/yishuship:use-yishuship
```

The router reads current `.ship/` state when present, reads the Matt flow
standard for non-trivial work, then chooses one route or asks one blocking
question. When a phase maps to Matt, the phase reads the corresponding
`vendor/mattpocock-skills/**/SKILL.md` before executing that lane.

## Command Map

| User intent | Command | Result |
|---|---|---|
| Raw product idea, new feature, market/product question | `/yishuship:pm-intake` | Product type, research, definition, PRD, test seams, decisions |
| Direct use of Matt upstream skills | `/yishuship:matt` | Reads the selected vendored Matt `SKILL.md` and applies it in yishuship |
| Need a plan for an already framed change | `/yishuship:design` | Adversarial design, executable plan, vertical slices |
| Implement an existing plan or issue | `/yishuship:dev` | One slice at a time, TDD loop, implementation evidence |
| Add durable acceptance tests | `/yishuship:e2e` | E2E tests, run logs, artifacts, regression coverage |
| Static review or bug inspection | `/yishuship:review` | Standards + Spec findings, severity-ranked issues |
| Runtime verification | `/yishuship:qa` | Manual/exploratory evidence against a running app |
| Architecture refactor / codebase entropy | `/yishuship:refactor` | Deep-module opportunities and scoped refactor plan |
| Detailed architecture after direction is chosen | `/yishuship:arch-design` | Design doc under `docs/design/` |
| Structured docs | `/yishuship:write-docs` | Managed docs under `docs/`, index updated |
| Visual system | `/yishuship:visual-design` | `DESIGN.md` and preview HTML |
| Release, PR, CI continuation, context transfer | `/yishuship:handoff` | Handoff/PR/CI artifacts without duplicating existing files |
| Full delivery | `/yishuship:auto` | PM → design → dev → e2e → review → qa → handoff |

## Triggers

yishuship should trigger when the user says or implies:

- "I have an idea", "build a product", "add a feature", "should we do this?"
- "choose an architecture", "which stack", "X or Y?"
- "plan this", "design this", "make a spec"
- "implement this", "fix this", "make it high quality"
- "test this", "does it work?", "add E2E"
- "review this", "find bugs", "is this safe to ship?"
- "refactor", "architecture is messy", "codebase is hard to change"
- "release", "make PR", "continue in another session"

The router should not ask the user to pick a phase when context is enough to
infer one.

## Matt Upstream Runtime

Matt's skills are active in two ways:

1. Phase skills read the relevant upstream Matt `SKILL.md` automatically.
2. `/yishuship:matt` lets the user invoke Matt upstream directly by name.

Examples:

```text
/yishuship:matt use grill-with-docs for this idea
/yishuship:matt run to-prd on our conversation
/yishuship:matt use tdd for this issue
/yishuship:matt use code-review on this diff
```

The vendored Matt files remain unmodified under `vendor/mattpocock-skills/`.
yishuship supplies routing, artifact conventions, and verification gates around
them.

Runtime activation is tested by `benchmarks/test_matt_runtime_activation.py`,
which checks that each yishuship phase references the upstream Matt files it is
supposed to use.

## What It Produces

Substantial work writes artifacts under:

```text
.ship/tasks/<task_id>/
  input/idea.md
  product/*
  delivery/design-spec.md
  control/lifecycle-checklist.yaml
  plan/*
  control/run_state.yaml
  e2e/report.md
  qa/*
  dev-context.md
```

Durable decisions go under:

```text
docs/decisions/DEC-NNNN-*.md
```

Operational docs go under:

```text
docs/operations/
```

## What It Should Not Do

- Do not jump from a raw idea straight to code.
- Do not skip product alignment when intent, users, value, or scope are unclear.
- Do not choose architecture inside detailed engineering design; architecture
  selection belongs in PM intake.
- Do not split implementation by horizontal layers when a vertical slice is
  possible.
- Do not mark work complete without verification evidence.
- Do not leave decisions only in chat.

## Current Quality Status

As of 2026-07-02, Matt flow triggering is measured by SkillOpt:

- Test split: `n=7`
- Overall after PM design seed fix: hard=`1.0`, soft=`0.9841`
- Matt flow held-out samples: `flow_test_001` and `flow_test_002` both pass
  with soft=`1.0`

The earlier weak point was old PM design artifact quality: `pm_005` failed
because the seed skill could refuse in benchmark mode and did not spell out the
design-stage checkpoints. The seed now has benchmark-mode instructions and an
explicit design-stage template; `pm_005` now passes with hard=`1`, soft=`1.0`.

After runtime activation, current qualitative score is `8.8/10`: Matt upstream
skills are both vendored and actively loaded by yishuship phases, with direct
access through `/yishuship:matt`.
