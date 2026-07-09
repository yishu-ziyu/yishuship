# Peer Spec

## Problem

The hardening slice must finish the migration from YAML to JSON for the product lifecycle entry artifact while keeping migration fallback behavior safe.
It must also connect that migration to checksum validation, PM handoff enforcement, stop-gate timeout handling, and long-horizon E2E coverage.
The active task is already past PM intake and in the design phase, so the remaining work is implementation hardening and consistency cleanup rather than product artifact creation.

## Design Approach

Make `product/00-product-type.json` the only forward-looking instruction path.
Keep runtime compatibility by accepting either JSON or legacy YAML in gate scripts during migration.
Treat `.ship` control artifacts as integrity-sensitive and validate them before successful phase transitions and guarded `.ship` writes.
Require the minimum PM handoff before design, dev, or subagent source writes.
Use script CLIs and hook JSON payloads as the main verification seam.

## Investigation Findings

`skills/.shared/product-lifecycle-21.md:20-39` already defines `product/00-product-type.json` in the standard task layout.
`skills/.shared/product-lifecycle-21.md:58-83` already documents the product type gate as JSON.
`skills/.shared/product-lifecycle-21.md:146-156` already lists JSON in the engineering gate.
`scripts/pm-gate.sh:39-51` accepts JSON or YAML for product type and requires the minimum V2 handoff files.
`scripts/pm-gate.sh:69-83` uses JSON-first block copy for design, auto, and dev gates.
`scripts/pm-verify.sh:48-76` accepts JSON or YAML while presenting JSON as the missing artifact name.
`scripts/phase-guardrail.sh:117-148` blocks subagent source writes until a PM handoff exists.
`scripts/phase-guardrail.sh:160-181` blocks `.ship` writes when checksum validation fails.
`scripts/validate-artifacts.sh:55-67` parses `--task`, but `scripts/validate-artifacts.sh:78-109` still loops over every manifest key without filtering other task directories.
That is a gap against the advertised task-scoped mode.
`scripts/stop-gate.sh:330-361` stores verifier output in `VERIFIER_CONTENT`, but the later verdict parsing still uses the temporary filename variable.
That is a likely correctness bug for TASK_COMPLETE, TASK_INCOMPLETE, and TASK_BLOCKED paths.
`benchmarks/test_long_horizon_e2e.py:717-827` covers checksum validation but does not cover task-scoped checksum filtering.
`benchmarks/test_long_horizon_e2e.py:675-693` covers timeout behavior but not successful or incomplete verifier verdict parsing.
`docs/superpowers/specs/2026-06-29-yishuship-v2-lifecycle-design.md:93-110` and `docs/superpowers/plans/2026-06-29-yishuship-v2-lifecycle.md:78-111` still contain YAML-first lifecycle instructions.
These docs should be marked historical or updated so they do not re-seed YAML-first behavior.

## Changes by File

- `scripts/validate-artifacts.sh`: implement actual task-scoped filtering for `--check --task <id>`.
- `scripts/stop-gate.sh`: parse verifier verdicts from `VERIFIER_CONTENT`, not the removed temp file path.
- `benchmarks/test_long_horizon_e2e.py`: add failing tests for task-scoped checksum filtering and verifier verdict parsing.
- `docs/superpowers/specs/2026-06-29-yishuship-v2-lifecycle-design.md`: mark the YAML references as historical or update them.
- `docs/superpowers/plans/2026-06-29-yishuship-v2-lifecycle.md`: mark the YAML references as historical or update them.
- `benchmarks/__pycache__/pm_scorer.cpython-313.pyc`: restore generated cache noise so it is not part of the intentional diff.

## Acceptance Criteria

- New task instructions point to `product/00-product-type.json`.
- Runtime gates continue accepting JSON or legacy YAML during migration.
- `bash scripts/validate-artifacts.sh --check --task <id> --json` ignores mismatches from other task directories while still checking global entries and the selected task.
- `bash scripts/validate-artifacts.sh --check --json` still blocks on any tracked mismatch.
- `scripts/stop-gate.sh` allows TASK_COMPLETE verifier output and removes the active state file.
- `scripts/stop-gate.sh` blocks TASK_INCOMPLETE verifier output and includes the missing item text.
- Stop-gate timeout behavior remains covered and fast in tests.
- Long-horizon and full benchmark suites pass.
- Remaining `00-product-type.yaml` search hits are only runtime compatibility or explicitly historical documentation.
- Generated Python cache changes are absent from the final intentional diff.

## Test Plan

Run `python3 -m pytest benchmarks/test_long_horizon_e2e.py -v --tb=short`.
Run `python3 -m pytest benchmarks/ -v --tb=short`.
Run `bash scripts/update-checksums.sh --init && bash scripts/validate-artifacts.sh --check --json` after legitimate `.ship` artifact changes.
Run `rg -n "00-product-type\.yaml" scripts skills docs benchmarks .ship/tasks/20260701-yishuship-sync-infra .ship/tasks/continue-yishuship-transformation-work-after-migrating-produ` and classify remaining hits.
Run `git status --short` and confirm no modified generated `.pyc` file remains.

## Risks

Task-scoped checksum filtering can be too broad if it suppresses global state mismatches.
The safer behavior is to skip only other `.ship/tasks/<other_id>/` entries while still checking global manifest entries.
Stop-gate timeout changes should not break successful verifier paths.
Historical docs should not be rewritten so aggressively that they lose audit value.
