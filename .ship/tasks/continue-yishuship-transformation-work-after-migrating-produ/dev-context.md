# Dev Context

## Test Command

Primary targeted command:

```bash
python3 -m pytest benchmarks/test_long_horizon_e2e.py -v --tb=short
```

Full regression command:

```bash
python3 -m pytest benchmarks/ -v --tb=short
```

## Test Seams

Use script CLIs and hook JSON payloads as public seams.
The checksum seam is `scripts/validate-artifacts.sh --check [--json] [--task <id>]` and `scripts/update-checksums.sh --init`.
The stop-gate seam is `scripts/stop-gate.sh` receiving hook JSON on stdin with verifier behavior controlled by `SHIP_AUTO_VERIFIER_CMD`.
The phase guardrail seam is `scripts/phase-guardrail.sh` receiving subagent tool-call JSON on stdin.

## Code Conduct

Follow `AGENTS.md`: yishuship artifacts live under `.ship/tasks/<task_id>/`; decisions live under `docs/decisions/`; non-trivial workflows follow `skills/.shared/matt-pocock-standard.md`.
Follow surrounding shell style: small Bash helpers, explicit `set -u`, jq for JSON, concise comments explaining workflow rules.
Follow test style in `benchmarks/test_long_horizon_e2e.py`: Python unittest classes executed through pytest, temporary git repositories, hook JSON through `run_hook()`, and stdout JSON assertions via `is_blocked()`.
Do not commit or push in this task.

## Pattern References

### Story 0: Verify active PM handoff and design transition

- Reference: `benchmarks/test_long_horizon_e2e.py`
  - Why analogous: Existing tests inspect `.ship` task artifacts and orchestrator prompts from temp repos.
  - Mirror: Use file existence checks and exact command expectations.
  - Deviations: The active handoff verification is a local validation step, not a new permanent test.

### Story 1: Task-scoped checksum filtering and guardrail blocking

- Reference: `benchmarks/test_long_horizon_e2e.py`
  - Why analogous: `TestArtifactIntegrity` already covers valid, tampered, missing, and non-ship checksum cases.
  - Mirror: Add tests in the same class using temp repos and subprocess calls to the real scripts.
  - Deviations: New tests create two task directories to prove task filtering ignores only other task entries.

- Reference: `scripts/validate-artifacts.sh`
  - Why analogous: This is the checksum module and already parses `--task`.
  - Mirror: Keep filtering inside `do_check()` and preserve global entry checks.
  - Deviations: Add a local helper to hide task-dir filtering behind the CLI interface.

- Reference: `scripts/phase-guardrail.sh`
  - Why analogous: Rule 6 already invokes checksum validation before `.ship` writes.
  - Mirror: Test through hook JSON instead of sourcing private functions.
  - Deviations: New test checks checksum mismatch behavior explicitly.

### Story 2: Stop-gate verifier verdict parsing

- Reference: `benchmarks/test_long_horizon_e2e.py`
  - Why analogous: `TestStopGate` already sets up a live `.ship/ship-auto.local.md` and feeds stop hook JSON.
  - Mirror: Add tests to the same class and control verifier behavior with environment variables.
  - Deviations: Import `os` so subprocess environments can preserve the current environment plus verifier overrides.

- Reference: `scripts/stop-gate.sh`
  - Why analogous: This is the session-exit verifier module.
  - Mirror: Keep timeout logic unchanged, only route parsed verdict and sections through captured verifier content.
  - Deviations: None.

### Story 3: Historical YAML-first superpowers docs

- Reference: `docs/superpowers/plans/2026-06-29-yishuship-v2-lifecycle.md`
  - Why analogous: Dated implementation plan with YAML-first historical content.
  - Mirror: Add a top historical note instead of rewriting old content.
  - Deviations: Current canonical protocol remains in `skills/.shared/product-lifecycle-21.md`.

- Reference: `docs/superpowers/specs/2026-06-29-yishuship-v2-lifecycle-design.md`
  - Why analogous: Dated design spec with YAML-first historical content.
  - Mirror: Add the same top historical note.
  - Deviations: None.

### Story 4: Cache cleanup and integrity baseline

- Reference: `benchmarks/__pycache__/pm_scorer.cpython-313.pyc`
  - Why analogous: Generated Python cache file appears modified but is not source.
  - Mirror: Verify it is generated cache before restoring it from git.
  - Deviations: Do not restore any non-generated source file without inspection.

## Waves

Sequential wave structure is safest because tasks touch shared test files and shell scripts.

1. Wave 1: Active handoff verification.
2. Wave 2: Add red tests for checksum task-scope and guardrail checksum mismatch.
3. Wave 3: Implement checksum task filtering.
4. Wave 4: Add red tests for stop-gate verifier verdicts.
5. Wave 5: Implement stop-gate verifier content parsing.
6. Wave 6: Add historical notes to dated docs.
7. Wave 7: Restore generated cache, refresh checksums, run full verification.
