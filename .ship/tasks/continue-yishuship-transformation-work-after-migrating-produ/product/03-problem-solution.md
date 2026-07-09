# Problem and Solution

## Problem Summary

yishuship has reached the point where workflow correctness depends on files and hooks, not just skill text.
The system can fail if a new PM task writes YAML while new tools expect JSON, if `.ship` control files are silently corrupted, if a subagent writes source code before PM handoff is complete, or if a stop verifier hangs and leaves the session stuck.
These failures all damage the same promise: `/yishuship:auto` should carry a product idea through staged delivery without losing process integrity.

## Severity and Frequency

Severity is high because a single state or guardrail failure can let agents skip product intent, mutate source prematurely, or misreport completion.
Frequency is expected to rise as yishuship is dogfooded on longer tasks and more agents participate.
The risk is especially high around context compaction, session resume, and branch switching.

## Solution Idea

Harden the workflow at the deterministic layer.
New product lifecycle tasks should write `product/00-product-type.json`.
Compatibility code should still read legacy YAML during migration.
Selected `.ship` control files should be recorded in `.ship/.checksums` and verified before phase transitions or guarded writes.
Subagents should be blocked from source writes until PM handoff exists.
Stop-gate verifier execution should time out cleanly rather than hanging forever.
A long-horizon E2E benchmark should exercise the full safety surface.

## Evidence

The current branch already contains the implementation direction in scripts and benchmark files.
The existing `20260701-yishuship-sync-infra` task proves that product artifacts can be migrated to JSON while preserving prior handoff content.
The generated `/yishuship:auto` prompt for this task explicitly names the required outcomes: JSON lifecycle state, artifact checksums, and a long-horizon E2E safety net.

## Non-goals

This slice does not create a recurring daemon or LaunchAgent.
It does not remove all YAML fallback paths.
It does not redesign every yishuship phase.
It does not publish, push, or merge changes unless the user explicitly asks.
