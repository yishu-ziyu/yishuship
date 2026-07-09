# Diff Report

## Divergence 1: Task-scoped checksum checks

Host spec initially said checksum scripts must support task-scoped checks, but did not call out the implementation gap.
Peer spec found that `scripts/validate-artifacts.sh` parses `--task` but still checks every manifest entry.

Evidence:

- `scripts/validate-artifacts.sh:13` advertises `--check --task <id>`.
- `scripts/validate-artifacts.sh:63` parses the option.
- `scripts/validate-artifacts.sh:78` loops over every manifest key without filtering non-selected task entries.

Disposition: conceded.
The merged spec now requires task-scoped filtering that skips only other `.ship/tasks/<other_id>/` entries while still checking global entries.

## Divergence 2: Stop-gate verifier output parsing

Host spec initially focused on verifier timeout behavior.
Peer spec found a likely correctness bug in normal verifier verdict parsing.

Evidence:

- `scripts/stop-gate.sh:330` reads verifier output into `VERIFIER_CONTENT`.
- `scripts/stop-gate.sh:331` removes the temporary output file.
- `scripts/stop-gate.sh:360`, `scripts/stop-gate.sh:368`, `scripts/stop-gate.sh:374`, and `scripts/stop-gate.sh:395` still pass `VERIFIER_OUTPUT`, which is the old temp file path rather than the verifier text.

Disposition: conceded.
The merged spec now requires tests for TASK_COMPLETE and TASK_INCOMPLETE paths and a fix to parse `VERIFIER_CONTENT`.

## Divergence 3: Historical YAML-first docs

Host spec planned to classify remaining YAML references.
Peer spec identified two dated superpowers docs that still contain YAML-first lifecycle instructions.

Evidence:

- `docs/superpowers/specs/2026-06-29-yishuship-v2-lifecycle-design.md:93` says `product/00-product-type.yaml` is the checklist entry.
- `docs/superpowers/plans/2026-06-29-yishuship-v2-lifecycle.md:78` lists `00-product-type.yaml` in the standard layout.
- `skills/.shared/product-lifecycle-21.md:20` and `skills/pm-intake/SKILL.md:101` are now JSON-first and are the active protocol sources.

Disposition: patched.
The plan will mark the two superpowers docs as historical snapshots instead of rewriting their whole contents.

## Divergence 4: Long-horizon E2E scope

Host spec treated long-horizon E2E as already present but needing verification.
Peer spec clarified that the suite covers many cases but misses task-scoped checksum filtering and normal verifier verdict parsing.

Evidence:

- `benchmarks/test_long_horizon_e2e.py:717` starts checksum integrity tests.
- `benchmarks/test_long_horizon_e2e.py:675` covers verifier timeout.
- No current search hit covers `SHIP_AUTO_VERIFIER_CMD` or `--task` in the benchmark suite.

Disposition: patched.
The plan adds focused regression tests for those two missing seams.
