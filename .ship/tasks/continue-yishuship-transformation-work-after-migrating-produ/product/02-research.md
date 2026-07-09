# Research

## Scenario Research

The key scenario is a long-running `/yishuship:auto` task that passes through PM intake, design, development, E2E, review, QA, refactor, and handoff.
This scenario is fragile because different agents and hooks read and write `.ship` artifacts at different moments.
The user may also clear, compact, or resume the session while work is mid-flight.
The workflow therefore needs deterministic state files, explicit artifact validation, and guardrails that catch unsafe writes even when an agent tries to move faster than the staged process.

## Current Workflow

The current repository already has a staged orchestrator in `scripts/auto-orchestrate.sh` and phase gates in `scripts/pm-gate.sh`, `scripts/pm-verify.sh`, `scripts/phase-guardrail.sh`, and `scripts/stop-gate.sh`.
An existing task, `20260701-yishuship-sync-infra`, has product lifecycle artifacts and a migrated `product/00-product-type.json`.
The current branch is dirty and contains changes for JSON migration, checksum scripts, guardrail hardening, stop-gate timeout behavior, and a long-horizon benchmark file.
The installed plugin and repo head are aligned at `c5f3796`, with `skill_links: 14/14`, so the active problem is not remote sync drift.
The active problem is finishing and validating the hardening slice that is already in progress.

## Existing Alternatives

The main alternative is prompt-level instruction: ask phase skills not to edit state files incorrectly and ask agents to respect PM handoff.
That is insufficient because the failure modes are tool-level and state-level, not just reasoning-level.
Another alternative is to remove old YAML support immediately and require all tasks to be migrated in one cut.
That is riskier than a compatibility window because historical `.ship/tasks/*` artifacts may still be useful for resume, audit, or memory.
A third alternative is to skip checksum protection and rely only on git diffs.
That fails during cross-session workflows where state files can be changed by hooks or agents before the user inspects the diff.

## Evidence

- `scripts/auto-orchestrate.sh` now has JSON-or-YAML artifact validation for the product type file.
- `scripts/validate-artifacts.sh` and `scripts/update-checksums.sh` implement the checksum manifest workflow.
- `scripts/phase-guardrail.sh` contains a PM handoff check for subagent source writes and a checksum check before `.ship/*` writes.
- `scripts/stop-gate.sh` is being hardened so verifier timeout does not hang a session indefinitely.
- `benchmarks/test_long_horizon_e2e.py` covers the long-horizon workflow behaviors that normal unit tests would miss.
