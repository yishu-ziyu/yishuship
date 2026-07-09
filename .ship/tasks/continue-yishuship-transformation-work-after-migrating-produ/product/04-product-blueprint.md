# Product Blueprint

## Product Solution

The product solution is a hardening layer for yishuship's staged delivery workflow.
It standardizes new product type artifacts on JSON, keeps legacy YAML readable, protects key `.ship` control files with checksums, blocks premature subagent source edits, and verifies the behavior with long-horizon E2E tests.
The user-facing result is not a new UI.
The user-facing result is a more trustworthy `/yishuship:auto` run: if the workflow is not ready to proceed, it blocks with a specific reason; if it proceeds, the artifact trail can be checked.

## Positioning

yishuship is positioned as a production delivery OS for one user plus many coding agents.
This slice strengthens the OS-level rules.
It is not about one feature surface; it is about making every future feature safer to execute.

## Core Flow

1. `/yishuship:auto` initializes or resumes a task.
2. `pm_intake` writes JSON product type and complete handoff artifacts.
3. The orchestrator validates required handoff files before dispatching design.
4. Subagents are allowed to modify source only after the PM handoff exists.
5. `.ship` control files are checked against the integrity manifest before risky transitions or guarded writes.
6. Stop-gate verifier work times out cleanly and returns actionable feedback.
7. Long-horizon E2E tests prove the guardrails across session-like transitions.

## Evolution Blueprint

Immediate slice: finish JSON migration, checksum scripts, guardrail behavior, stop-gate timeout, and E2E coverage.
Next slice: decide whether and when to remove YAML fallback after old tasks are either migrated or intentionally archived.
Later slice: add operational guidance around checksum re-baselining and plugin sync dogfood.
Future slice: add analytics only if yishuship starts producing enough repeated workflow data to learn from.

## Scope Boundary

In scope: scripts, skill docs, task artifacts, checksum manifest, and benchmark tests that support the current hardening goal.
Out of scope: unrelated skill rewrites, marketplace cleanup, LaunchAgent automation, public release packaging, and full historical task migration.
