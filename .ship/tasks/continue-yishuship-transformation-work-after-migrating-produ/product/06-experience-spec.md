# Experience Spec

## Key Screens

There is no graphical UI in this slice.
The key user-visible surfaces are CLI output, hook block messages, task artifact paths, and benchmark output.
The auto orchestrator should emit `ACTION`, `PHASE`, `PROMPT_FILE`, and `MESSAGE` consistently.
Guardrail blocks should explain the exact missing condition, such as incomplete PM handoff or checksum mismatch.
Checksum tools should print concise allow/block JSON in hook mode and readable diagnostics in CLI mode.

## Core States

- No active task: `scripts/auto-orchestrate.sh status` reports no active task.
- PM intake running: task directories exist, but PM handoff may be incomplete.
- PM handoff complete: required product and plan artifacts exist and `.ship/pm-state.yaml` has `phase: complete` for the active task.
- Engineering allowed: subagent source writes are permitted only after PM handoff validation passes.
- Integrity clean: `.ship/.checksums` matches tracked control files.
- Integrity mismatch: guarded `.ship` writes and phase transitions are blocked until legitimate changes are re-baselined.
- Verifier timeout: stop gate returns a controlled block message rather than hanging indefinitely.

## Empty, Loading, Error States

If the checksum manifest does not exist, validation should behave as an empty manifest rather than crashing.
If a legacy YAML product type file exists, validation should accept it during migration.
If neither JSON nor YAML product type exists, PM intake validation should fail with a specific missing artifact message.
If a subagent tries to modify source before PM handoff, the guardrail should block and list the required handoff artifacts.
If the verifier times out, the stop gate should block with a clear continuation instruction.

## Golden Journeys

Golden journey 1: A new `/yishuship:auto` task writes `product/00-product-type.json`, completes PM handoff, and moves to design.
Golden journey 2: A legacy task with `product/00-product-type.yaml` still validates during migration.
Golden journey 3: A subagent source write before PM handoff is blocked.
Golden journey 4: A legitimate `.ship` control update is followed by checksum update and future checks pass.
Golden journey 5: A hung verifier exits through timeout handling and does not leave the user trapped.
Golden journey 6: Long-horizon E2E tests exercise the workflow and pass before handoff.
