---
name: auto
description: >
  Run yishuship's full production workflow from raw requirement to PR: pm-intake(product lifecycle) → design → dev → e2e → review → qa → refactor → handoff. Growth Loop is optional continuation after handoff, not mandatory. Use only for explicit /yishuship:auto,
  auto pipeline requests, or end-to-end delivery.
allowed-tools:
  - Bash
  - Read
  - Agent
  - TodoWrite
---

# yishuship: Auto

Full staged workflow for explicit end-to-end production delivery.
pm-intake(product lifecycle) → design → dev → e2e → review → qa → refactor → handoff

Growth Loop is optional continuation after handoff, not mandatory.

Read `../.shared/matt-pocock-standard.md` and
`../../vendor/mattpocock-skills/skills/engineering/ask-matt/SKILL.md` before
starting. `/yishuship:auto` is yishuship's user-invoked orchestrator over the
same main-flow shape:
alignment → PRD/seams → vertical slices → TDD implementation → review → ship.

## Hard Rules

- The orchestrator owns `.ship/ship-auto.local.md`; do not edit it manually.
- Do not dispatch design until the orchestrator emits `PHASE:pm_intake` and then accepts `pm_intake:success`.
- Do not skip Matt's alignment/shared-language layer; `pm_intake` must settle product intent, key terms, and hard-to-reverse decisions before engineering.
- If a design question needs a runnable answer, create a prototype branch through `design`/`dev` and preserve the answer in artifacts before continuing.
- Do not claim completion unless the orchestrator emits `ACTION:done`.
- If the orchestrator emits `ACTION:escalate`, stop and report the blocker instead of continuing by hand.

## Steps

1. Resolve `../../scripts/auto-orchestrate.sh` relative to this skill file.
2. Run the shared stage-aware orchestrator:

```bash
SHIP_ORCH="../../scripts/auto-orchestrate.sh"
if [ -f .ship/ship-auto.local.md ]; then
  "$SHIP_ORCH" resume
else
  "$SHIP_ORCH" init '<user requirement goes here>'
fi
```

3. Read `PROMPT_FILE`, dispatch the agent with that prompt, classify the report card, and call `complete <PHASE>`.
4. Repeat until the orchestrator emits `ACTION:done` or `ACTION:escalate`.

## Product Lifecycle Gate

The orchestrator starts with `pm_intake`, reuses the same `task_id`, and validates
the V2 product lifecycle artifacts before dispatching design. PM Gate remains a
second safety net for direct engineering skill invocations.

## Completion Gate

Done means the orchestrator has written or preserved `.ship/tasks/<task_id>/`
artifacts for each completed phase and emitted `ACTION:done`. Anything else is
`BLOCKED` or still running.

## [Auto] Report Card

| Field | Value |
|-------|-------|
| Status | <DONE / BLOCKED> |
| Task | <task_id> |
| Final action | <ACTION:done / ACTION:escalate> |
| Current phase | <phase> |
| Artifacts | `.ship/tasks/<task_id>/` |

## Standalone Skill Boundary

`/yishuship:auto` is only for full production workflow runs. If the user asks for a
specific phase such as design, development, E2E, review, QA, refactor, or
handoff, invoke that standalone `/yishuship:*` skill directly instead of routing
through auto.
