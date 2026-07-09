# Engineering Spec

## Goal

Finish the yishuship long-horizon workflow hardening slice so `/yishuship:auto` can safely continue across JSON product lifecycle migration, `.ship` checksum validation, subagent PM handoff enforcement, stop-gate verifier timeout, and cross-session resume.

## Requirements

1. New lifecycle task prompts and docs must require `product/00-product-type.json`.
2. Runtime validation must accept either `product/00-product-type.json` or legacy `product/00-product-type.yaml` during migration.
3. The active auto PM handoff must contain product artifacts `00` through `09`, `control/lifecycle-checklist.yaml`, `delivery/design-spec.md`, and this `plan/spec.md`.
4. `.ship/pm-state.yaml` must reference the active task and `phase: complete` after PM intake.
5. Checksum scripts must initialize, update, and check selected `.ship` control files.
6. Guardrails must block subagent source writes before PM handoff is complete.
7. Guardrails must block `.ship` writes when checksum validation reports a mismatch.
8. Stop gate verifier execution must time out with a controlled message.
9. Long-horizon E2E tests must cover the new workflow safety behavior.
10. Generated Python cache changes must be absent from the final intentional diff.

## Acceptance Criteria

- `bash scripts/validate-artifacts.sh --check --json` prints an allow decision after the final checksum baseline update.
- `python3 -m pytest benchmarks/test_long_horizon_e2e.py -v --tb=short` passes.
- `python3 -m pytest benchmarks/ -v --tb=short` passes.
- `git status --short` shows no modified generated `benchmarks/__pycache__/pm_scorer.cpython-313.pyc`.
- `scripts/auto-orchestrate.sh complete pm_intake --verdict=success` can advance this task from PM intake to design after required artifacts and `.ship/pm-state.yaml` are present.
- Remaining `00-product-type.yaml` references are either legacy compatibility code or historical artifact references, not new-task instructions.

## Test Seams

Use script CLIs and hook JSON payloads as the main test seams.
They are the highest seams that match user-visible yishuship behavior.
Avoid testing only helper internals when a script command can exercise the same behavior.

## Out of Scope

Removing YAML fallback is out of scope.
Migrating every historical task is out of scope.
Adding a daemon or analytics loop is out of scope.
Committing and pushing are out of scope unless requested.

## Design Investigation

The shared lifecycle reference already uses `product/00-product-type.json` in the standard task layout and product type gate at `skills/.shared/product-lifecycle-21.md:20` and `skills/.shared/product-lifecycle-21.md:58`.
The PM gate already has a small product type interface that accepts JSON or YAML and requires the minimum V2 handoff at `scripts/pm-gate.sh:39`.
The PM verifier mirrors that migration behavior and reports the JSON path when the artifact is missing at `scripts/pm-verify.sh:48`.
The phase guardrail already has the important PM handoff seam for subagent source writes at `scripts/phase-guardrail.sh:117`, and the checksum guard for `.ship` writes at `scripts/phase-guardrail.sh:160`.
The checksum module advertises task-scoped checks at `scripts/validate-artifacts.sh:13`, parses `--task` at `scripts/validate-artifacts.sh:63`, but still loops every manifest key at `scripts/validate-artifacts.sh:78`; this needs a real filter.
The stop gate stores verifier output in `VERIFIER_CONTENT` at `scripts/stop-gate.sh:330`, but successful verdict parsing still reads `VERIFIER_OUTPUT` at `scripts/stop-gate.sh:360`; after cleanup that variable is just the temp file path, so successful and incomplete verifier paths need coverage and a fix.
The long-horizon E2E suite already covers checksum validation at `benchmarks/test_long_horizon_e2e.py:717` and timeout behavior at `benchmarks/test_long_horizon_e2e.py:675`, but not task-scoped checksum filtering or normal verifier verdict parsing.

## Final Design Decisions

Keep JSON as the canonical new product lifecycle entry artifact.
Keep YAML fallback in runtime gates during migration.
Treat `validate-artifacts.sh` as the deep module for checksum behavior, with a small CLI interface and all manifest filtering hidden inside the implementation.
Treat `stop-gate.sh` as the deep module for session-exit verification, with hook JSON as the test seam.
Add regression tests before fixing the two behavior gaps so future changes cannot silently reintroduce them.
Mark old superpowers lifecycle docs as historical instead of rewriting their entire content, because those files are dated design records rather than the canonical current protocol.
