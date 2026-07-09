# Technical and Project Plan

## Technical Plan

Use the existing shell-script architecture rather than introducing a new runtime.
Keep `scripts/auto-orchestrate.sh` as the phase state machine.
Add a small `require_json_or_yaml` helper so validation can prefer JSON without breaking legacy YAML tasks.
Use `scripts/validate-artifacts.sh` for checksum check, update, and init modes.
Keep `scripts/update-checksums.sh` as a thin wrapper for user-facing re-baselining.
Integrate checksum checks into the orchestrator and phase guardrail at the points where state corruption would be expensive.
Add deterministic benchmark coverage in `benchmarks/test_long_horizon_e2e.py`.
Keep user-facing skill docs aligned with the new JSON artifact name.

## Architecture Decision

The chosen architecture is deterministic shell enforcement plus benchmark tests.
This is better than pure skill text because the critical failure modes happen at tool and file boundaries.
It is better than introducing a service because yishuship is currently a local Claude Code plugin and should remain inspectable and easy to dogfood.
The checksum manifest deliberately tracks selected control files, not every product artifact, because product and delivery artifacts are expected to be edited by agents and users.

## Project Plan

1. Finish product handoff artifacts for this auto task.
2. Finish or verify JSON migration across scripts, prompts, docs, and existing task artifacts.
3. Finish or verify checksum script behavior and guardrail integration.
4. Finish or verify stop-gate timeout behavior.
5. Run targeted long-horizon E2E tests.
6. Run the full benchmark suite.
7. Refresh checksum baseline after legitimate `.ship` artifact changes.
8. Produce a handoff that names changed paths, verification status, and follow-up risks.

## Milestones

- PM handoff ready: required product, delivery, and plan artifacts exist for this task.
- Design ready: plan/spec and acceptance criteria are accepted by the orchestrator.
- Dev ready: source changes are complete and generated cache noise is removed or restored.
- E2E ready: targeted and full benchmark suites pass.
- Handoff ready: checksum validation passes and remaining risks are documented.

## Risks and Mitigations

Risk: JSON/YAML compatibility leaves stale references.
Mitigation: Search for `00-product-type.yaml` after implementation and decide whether each occurrence is legacy compatibility or stale documentation.

Risk: Checksum validation blocks legitimate work.
Mitigation: Keep manifest scope narrow, document re-baselining, and run long-horizon tests around mismatch and update flows.

Risk: Phase guardrail path matching misses a source write or blocks a valid artifact write.
Mitigation: Cover representative hook payloads in tests and keep exemptions explicit.

Risk: Stop-gate timeout behavior becomes platform-sensitive.
Mitigation: Test it through a deterministic sleeping verifier and avoid depending on non-portable process behavior where possible.

Risk: Generated `.pyc` changes pollute the diff.
Mitigation: Restore or ignore generated cache files before final verification.
