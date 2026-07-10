# DEC-0007: Execution model - serial deps, parallel inside, fail loops

> Date: 2026-07-10
> Status: Accepted

## Decision

yishuship runs work under three layers:

1. **Stage dependencies** - serial when upstream artifacts are required.
2. **Intra-stage parallel** - only when no write conflict and each unit is independently checkable.
3. **Failure loops** - fix and re-verify; escalate after budget; never fake completion.

Canonical text: `skills/.shared/execution-model.md`.

## Why

- Strict 9-step serial is too rigid and wastes time.
- Free-form parallel across stages destroys product/engineering truth.
- Industry loop/dynamic-workflow patterns help **inside** a stage; they do not erase dependencies.

## Consequences

- Router and auto must read `execution-model.md`.
- Phase skills keep their existing parallel patterns (design peer, dev waves) and name them as Layer 2.
- Auto keep `*_fix` loops as Layer 3; do not add cross-stage parallel fan-out by default.

## Non-goals

- Full Claude "dynamic workflows" runtime inside yishuship.
- SkillOpt as a runtime dependency.
