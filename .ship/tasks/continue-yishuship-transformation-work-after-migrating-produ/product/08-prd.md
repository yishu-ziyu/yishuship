# PRD

## Product Requirements

1. New PM intake output must use `product/00-product-type.json` for the product type artifact.
2. Validation must continue to accept legacy `product/00-product-type.yaml` during migration.
3. Documentation and skill prompts must refer to JSON as the canonical new artifact.
4. The orchestrator must validate all required PM handoff artifacts before dispatching design.
5. The orchestrator must run artifact integrity checks before successful phase transitions that depend on `.ship` state.
6. A checksum manifest must store SHA-256 values for selected `.ship` control files.
7. A checksum update script must provide an explicit way to initialize or update the manifest after legitimate changes.
8. The phase guardrail must block subagent source writes before PM handoff is complete.
9. The phase guardrail must block unsafe `.ship` writes when integrity checks fail.
10. The stop gate must time out verifier execution and return actionable feedback instead of hanging indefinitely.
11. A long-horizon E2E benchmark must cover PM gate, PM verify, phase guardrail, stop gate timeout, checksum scripts, and cross-session resume behavior.
12. The existing migrated task artifact `20260701-yishuship-sync-infra/product/00-product-type.json` must replace the YAML artifact.
13. Generated Python cache artifacts must not be part of the intentional source diff.

## Acceptance Criteria

- `scripts/auto-orchestrate.sh complete pm_intake --verdict=success` rejects missing product type artifacts and accepts either non-empty JSON or legacy YAML.
- A new `/yishuship:auto` PM prompt lists `product/00-product-type.json` as the required artifact.
- `scripts/pm-gate.sh` and `scripts/pm-verify.sh` accept the JSON product type artifact.
- `scripts/phase-guardrail.sh` blocks a subagent `Write` or `Edit` to source code when PM handoff is incomplete.
- `scripts/phase-guardrail.sh` does not block metadata or temp writes that are explicitly exempt.
- `scripts/validate-artifacts.sh --check --json` returns allow JSON when the manifest matches.
- `scripts/validate-artifacts.sh --check --json` returns block JSON when a tracked file is missing or tampered.
- `scripts/update-checksums.sh --init` initializes the manifest for selected existing control files.
- The stop gate timeout path is covered by a deterministic benchmark case.
- `python3 -m pytest benchmarks/test_long_horizon_e2e.py -v --tb=short` passes.
- `python3 -m pytest benchmarks/ -v --tb=short` passes before handoff.
- `bash scripts/validate-artifacts.sh --check --json` passes after the final checksum baseline update.

## Testing Seams

The highest useful seam is the script CLI seam, because yishuship's workflow behavior is exposed through shell scripts and hook JSON.
Tests should call scripts with representative hook payloads and inspect exit codes plus stdout.
For checksum behavior, tests should create or mutate temporary task artifacts and run the checksum scripts rather than only unit-testing hash helpers.
For stop-gate timeout, tests should use a controlled verifier command that sleeps beyond the configured timeout.
For cross-session resume, tests should exercise orchestrator state files and resume behavior from the repository root.

## Vertical Slice Candidates

1. JSON product type migration: docs, prompts, validation helper, existing task artifact, and targeted tests.
2. Artifact checksum integrity: validate script, update wrapper, guardrail integration, orchestrator integration, and tests.
3. Subagent PM handoff guardrail: missing-handoff block, allowed metadata paths, and tests.
4. Stop-gate timeout: timeout implementation and benchmark coverage.
5. Cleanup and verification: remove generated cache noise, refresh checksum baseline, run targeted and full benchmark suites.

## Edge Cases

Legacy tasks with YAML product type files should continue to pass migration-era validation.
A checksum manifest with no files should not fail normal checks.
A tracked checksum file deleted from disk should produce a clear missing-file mismatch.
A tracked checksum file modified outside the update protocol should produce a tampered mismatch.
A dirty worktree should not be silently treated as a clean finished state.
A stop verifier that exits quickly should not be affected by timeout logic.

## Out of Scope

Do not remove all YAML fallback support in this slice.
Do not migrate every historical task artifact.
Do not add a daemon, LaunchAgent, or analytics pipeline.
Do not commit or push unless the user asks.
