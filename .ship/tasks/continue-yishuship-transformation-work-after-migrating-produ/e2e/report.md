# E2E Report

## Framework

Framework: pytest.

Status: pre-existing.

Test location: `benchmarks/`.

This repository is a CLI and shell workflow project, not a browser UI app.
The durable E2E seam is subprocess-driven workflow tests that exercise script CLIs and hook JSON payloads.

## Tests Added or Modified

Modified `benchmarks/test_long_horizon_e2e.py`.

Added task-scoped checksum filtering coverage:

- `TestArtifactIntegrity::test_task_scoped_check_ignores_other_task_mismatches`
- `TestArtifactIntegrity::test_task_scoped_check_still_blocks_selected_task_mismatch`

Added checksum guardrail coverage:

- `TestPhaseGuardrail::test_blocks_ship_metadata_write_when_checksum_mismatch`

Added stop-gate verifier verdict coverage:

- `TestStopGate::test_verifier_task_complete_allows_exit_and_removes_state`
- `TestStopGate::test_verifier_task_incomplete_blocks_with_missing_items`

Added local-repo dev completion coverage:

- `TestCrossSessionResume::test_complete_dev_uses_pre_dev_sha_without_origin_head`

## Run Results

First red check for focused checksum and stop-gate tests:

```bash
python3 -m pytest benchmarks/test_long_horizon_e2e.py::TestArtifactIntegrity benchmarks/test_long_horizon_e2e.py::TestPhaseGuardrail benchmarks/test_long_horizon_e2e.py::TestStopGate -v --tb=short
```

Result: 3 failed, 22 passed.

The expected failures were task-scoped checksum filtering and stop-gate verifier content parsing.

Green focused check after fixes:

```bash
python3 -m pytest benchmarks/test_long_horizon_e2e.py::TestArtifactIntegrity benchmarks/test_long_horizon_e2e.py::TestPhaseGuardrail benchmarks/test_long_horizon_e2e.py::TestStopGate -v --tb=short
```

Result: 25 passed.

Green local-repo dev completion regression:

```bash
python3 -m pytest benchmarks/test_long_horizon_e2e.py::TestCrossSessionResume::test_complete_dev_uses_pre_dev_sha_without_origin_head -v --tb=short
```

Result: 1 passed.

Green long-horizon suite:

```bash
python3 -m pytest benchmarks/test_long_horizon_e2e.py -v --tb=short
```

Result: 57 passed.

Green full benchmark suite:

```bash
python3 -m pytest benchmarks/ -v --tb=short
```

Result: 68 passed.

Checksum validation:

```bash
bash scripts/validate-artifacts.sh --check --json
```

Result: `{"decision":"allow","reason":"all artifacts match"}`.

Whitespace validation:

```bash
git diff --check
```

Result: passed with no output.

## Failures

No remaining E2E failures.

The initial red failures were real regressions in workflow behavior and were fixed before this report.

## Regressions

No broader benchmark regressions were observed.

## Cleanup

No services, containers, browsers, or ports were started for this E2E phase.
No PID cleanup was required.
