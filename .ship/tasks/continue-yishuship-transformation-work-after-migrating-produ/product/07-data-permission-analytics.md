# Data, Permission, and Analytics

## Report Design

The main reports are the PM handoff artifacts, checksum validation output, E2E benchmark output, review notes, QA report, refactor report, and final handoff.
Checksum validation in hook mode should emit compact JSON with `decision`, `reason`, and mismatch details.
CLI mode should emit readable text suitable for debugging.
The final handoff should name the exact commands run and whether they passed.

## Tracking Plan

No product analytics are required in this slice.
The evidence trail is file-based and command-based:

- `.ship/.checksums` records artifact hashes.
- `control/run_state.yaml` records phase state.
- `control/lifecycle-checklist.yaml` records checkpoint applicability.
- Test output records whether gates and safety behavior pass.
- Git diff records implementation changes.

## Permission Model

The orchestrator owns `.ship/ship-auto.local.md`.
Subagents may write phase artifacts only inside their phase-owned `.ship/tasks/<task_id>/` paths.
Review and QA phases must not modify source code.
Subagents must not modify source code before PM handoff is complete.
Agents may update checksums only through the intended update script after legitimate artifact changes.
Destructive operations, deletion of existing user files, commit, push, and process-kill actions still require explicit user authorization.

## Risk Controls

Checksum protection reduces silent corruption risk but can introduce false positives if legitimate edits are not re-baselined.
To control that risk, the workflow should keep checksum scope focused on selected control files and expose `scripts/update-checksums.sh --init` as the explicit re-baseline operation.
JSON/YAML compatibility reduces migration breakage but temporarily increases logic branches.
To control that risk, new docs and new artifacts should point to JSON while scripts keep a small compatibility helper.
Subagent write blocking reduces premature implementation risk but may need path-matching tests to avoid false blocks.
The long-horizon E2E suite is the regression control for these risks.
