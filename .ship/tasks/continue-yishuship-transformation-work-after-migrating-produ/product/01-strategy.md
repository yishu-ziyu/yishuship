# Strategy

## BRD: Why This Is Worth Doing

yishuship is meant to make long product and engineering workflows reliable enough for a user to trust agents across many sessions.
The current hardening slice is worth doing because the workflow has moved beyond simple skill prompts into a stateful system with gates, artifacts, subagents, and cross-session resume.
If the state files drift, a subagent bypasses PM handoff, or a verifier hangs, the user experiences the same product failure: the system says it is disciplined but behaves like an ordinary loose chat workflow.
This slice makes the workflow more durable by moving new product type artifacts to JSON, protecting selected `.ship` control files with checksums, adding explicit subagent write guardrails, and covering the behavior with long-horizon E2E tests.

## MRD: Market, User, Competition

The primary user is one owner operating Claude Code with yishuship as a delivery operating system.
The secondary users are coding agents that need deterministic rails rather than relying on memory or prompt compliance.
The alternative is the original Ship-style flow plus manual discipline.
That alternative works for shorter tasks, but it does not fully protect against local plugin drift, stale state, accidental `.ship` mutation, or agents writing source code before the product handoff is ready.
The switching reason is trust.
The user should feel that `/yishuship:auto` can continue a multi-phase task without silently losing its contract.

## Switching Reason

Users would switch to this hardened behavior because it reduces the cognitive burden of supervising agent process integrity.
Instead of asking whether the agent remembered PM intake, updated state safely, or skipped verification, the workflow itself blocks unsafe paths and records evidence.

## Decision

- Do: Prefer `product/00-product-type.json` for new lifecycle tasks while keeping YAML fallback during migration.
- Do: Protect `.ship` control files with a checksum manifest and require explicit re-baselining after legitimate changes.
- Do: Block subagent source writes when PM handoff artifacts are incomplete.
- Do: Add long-horizon E2E coverage for gates, checksums, stop-gate timeout, and cross-session resume.
- Do not do: Remove YAML fallback immediately, because legacy tasks still exist and should remain readable.
- Do not do: Add analytics or recurring operations in this slice.
- Evidence: Current diff already touches `scripts/auto-orchestrate.sh`, `scripts/phase-guardrail.sh`, `scripts/pm-gate.sh`, `scripts/pm-verify.sh`, `scripts/stop-gate.sh`, `skills/.shared/product-lifecycle-21.md`, `skills/pm-intake/SKILL.md`, `skills/use-yishuship/SKILL.md`, and `benchmarks/test_long_horizon_e2e.py`.
