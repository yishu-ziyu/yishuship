# Engineering Design Spec

## Engineering Goal

Finish the yishuship long-horizon workflow hardening slice.
The goal is to make `/yishuship:auto` safer across JSON product lifecycle migration, `.ship` artifact integrity, PM handoff enforcement, stop-gate verifier timeout, and cross-session resume.

## Product Context

yishuship is a local Claude Code delivery workflow for one user and many coding agents.
The user depends on the workflow to enforce product thinking before engineering, keep phase artifacts durable, and avoid premature completion.
This slice is not a new end-user UI.
It is a reliability upgrade for the delivery operating system itself.

## Requirements

- New PM lifecycle tasks must use `product/00-product-type.json` as the canonical product type artifact.
- Legacy `product/00-product-type.yaml` must remain accepted during migration.
- Skill docs, prompt templates, and shared lifecycle docs must point new work to JSON.
- The auto orchestrator must validate PM handoff artifacts before leaving PM intake.
- The auto orchestrator must run artifact integrity checks before successful phase transitions.
- `scripts/validate-artifacts.sh` must support check, check JSON output, task-scoped check, update, and init modes.
- `scripts/update-checksums.sh` must be a clear wrapper for re-baselining checksum entries.
- `scripts/phase-guardrail.sh` must block subagent source writes before PM handoff completion.
- `scripts/phase-guardrail.sh` must block guarded `.ship` writes when checksum validation fails.
- `scripts/stop-gate.sh` must time out verifier execution cleanly.
- `benchmarks/test_long_horizon_e2e.py` must exercise the above workflow behaviors.
- Generated Python cache changes must not remain as intentional source changes.

## Acceptance Criteria

- The active PM intake task contains all required product artifacts, `delivery/design-spec.md`, and `plan/spec.md`.
- `.ship/pm-state.yaml` points to the active task and has `phase: complete`.
- `bash scripts/validate-artifacts.sh --check --json` returns allow JSON after final checksum update.
- `python3 -m pytest benchmarks/test_long_horizon_e2e.py -v --tb=short` passes.
- `python3 -m pytest benchmarks/ -v --tb=short` passes.
- The diff no longer contains generated `benchmarks/__pycache__/pm_scorer.cpython-313.pyc` changes.
- Searching for `00-product-type.yaml` leaves only intentional legacy compatibility references or clearly historical artifacts.

## Constraints

- Do not commit or push without explicit user request.
- Do not remove YAML fallback in this slice.
- Do not delete historical task artifacts except the specific migrated YAML artifact already replaced by JSON for the sync-infra task.
- Do not manually edit `CHANGELOG.md` or generated files.
- Keep changes surgical and aligned with existing shell-script conventions.

## Source Artifacts

- `.ship/tasks/continue-yishuship-transformation-work-after-migrating-produ/product/00-product-type.json`
- `.ship/tasks/continue-yishuship-transformation-work-after-migrating-produ/product/08-prd.md`
- `.ship/tasks/continue-yishuship-transformation-work-after-migrating-produ/product/09-tech-project-plan.md`
- `.ship/tasks/continue-yishuship-transformation-work-after-migrating-produ/plan/spec.md`
- `CONTEXT.md`
