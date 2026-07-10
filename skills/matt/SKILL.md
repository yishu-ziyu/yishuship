---
name: matt
description: >
  Direct runtime adapter for vendored Matt Pocock skills inside yishuship. Use
  when the user asks to use Matt's skills, names ask-matt, grill-me,
  grill-with-docs, to-spec, to-prd (alias), to-tickets, to-issues (alias),
  wayfinder, research, implement, tdd, diagnosing-bugs, domain-modeling,
  codebase-design, code-review, prototype, triage,
  improve-codebase-architecture, handoff, writing-great-skills, teach, or wants
  yishuship to apply Matt's original workflow rather than only yishuship's
  adapted phases.
---

# yishuship: Matt Upstream Adapter

This skill makes Matt's vendored skills active at runtime. It does not rewrite
or summarize them. It chooses the upstream `SKILL.md`, reads it completely, then
executes that skill's process in the current yishuship context.

Vendored line: package **1.1.0** (see `vendor/README.md`).

## Hard Rule

Always read the selected upstream `SKILL.md` before acting. The files under
`../../vendor/mattpocock-skills/` are the source of truth.

## Routing

| User intent / name | Upstream file |
|---|---|
| Which Matt flow fits? `ask-matt` | `../../vendor/mattpocock-skills/skills/engineering/ask-matt/SKILL.md` |
| Huge multi-session plan `wayfinder` | `../../vendor/mattpocock-skills/skills/engineering/wayfinder/SKILL.md` |
| General grilling / interview | `../../vendor/mattpocock-skills/skills/productivity/grill-me/SKILL.md` |
| Stateful grilling with project docs | `../../vendor/mattpocock-skills/skills/engineering/grill-with-docs/SKILL.md` |
| Reusable grilling loop | `../../vendor/mattpocock-skills/skills/productivity/grilling/SKILL.md` |
| Domain language / CONTEXT.md / ADRs | `../../vendor/mattpocock-skills/skills/engineering/domain-modeling/SKILL.md` |
| Spec / PRD `to-spec` (alias `to-prd`) | `../../vendor/mattpocock-skills/skills/engineering/to-spec/SKILL.md` |
| Tickets / vertical slices `to-tickets` (alias `to-issues`) | `../../vendor/mattpocock-skills/skills/engineering/to-tickets/SKILL.md` |
| Primary-source `research` | `../../vendor/mattpocock-skills/skills/engineering/research/SKILL.md` |
| Implement from ticket/spec | `../../vendor/mattpocock-skills/skills/engineering/implement/SKILL.md` |
| TDD / red-green-refactor | `../../vendor/mattpocock-skills/skills/engineering/tdd/SKILL.md` |
| Hard bug or performance regression | `../../vendor/mattpocock-skills/skills/engineering/diagnosing-bugs/SKILL.md` |
| Deep modules / seams / interface design | `../../vendor/mattpocock-skills/skills/engineering/codebase-design/SKILL.md` |
| Architecture health rescue | `../../vendor/mattpocock-skills/skills/engineering/improve-codebase-architecture/SKILL.md` |
| Prototype to answer a design question | `../../vendor/mattpocock-skills/skills/engineering/prototype/SKILL.md` |
| Two-axis code review | `../../vendor/mattpocock-skills/skills/engineering/code-review/SKILL.md` |
| Issue triage | `../../vendor/mattpocock-skills/skills/engineering/triage/SKILL.md` |
| Setup Matt skill config | `../../vendor/mattpocock-skills/skills/engineering/setup-matt-pocock-skills/SKILL.md` |
| Merge conflict resolution | `../../vendor/mattpocock-skills/skills/engineering/resolving-merge-conflicts/SKILL.md` |
| Cross-session handoff | `../../vendor/mattpocock-skills/skills/productivity/handoff/SKILL.md` |
| Skill quality / writing great skills | `../../vendor/mattpocock-skills/skills/productivity/writing-great-skills/SKILL.md` |
| Teaching over sessions | `../../vendor/mattpocock-skills/skills/productivity/teach/SKILL.md` |

## Execution

1. Read `../.shared/matt-pocock-standard.md`.
2. Select the smallest upstream Matt skill that fits the user request.
3. Map legacy names (`to-prd` → `to-spec`, `to-issues` → `to-tickets`) before open.
4. Read the selected upstream `SKILL.md` completely.
5. If that upstream skill points to relative files, resolve them relative to
   its own folder and read only the files the upstream skill says are needed.
6. Execute the upstream skill in the current repo, preserving yishuship's
   artifact conventions:
   - durable task artifacts in `.ship/tasks/<task_id>/`
   - decisions in `docs/decisions/`
   - shared language in `CONTEXT.md`
7. If the selected Matt flow conflicts with a yishuship phase rule, keep Matt's
   process discipline and yishuship's artifact/verification conventions.

## Completion Gate

Done means the selected upstream Matt skill was read and applied, and the final
answer names which upstream skill was used plus any artifacts, decisions, tests,
or blockers produced.
