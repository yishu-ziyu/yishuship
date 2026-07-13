# CLI Exploratory Report

| Field | Value |
|---|---|
| Date | 2026-07-13 |
| CLI | yishuship Bash entry points |
| Scope | artifact integrity, task-scoped checks, orchestration status, invalid input |

## Verdict

PASS — 4/4 direct CLI checks passed; no issues beyond the spec.

## Direct evidence

- Global integrity check returned `decision: allow`.
- Active-task scoped integrity check returned `decision: allow`.
- Orchestrator returned structured JSON with the expected task and `qa` phase.
- Unknown integrity command failed closed with exit code 1 and usage text.
- Full benchmark baseline: `87 passed in 52.88s`.

See `cli-core-paths.txt` for captured command output.

## Summary

| Severity | Count |
|---|---:|
| Critical | 0 |
| High | 0 |
| Medium | 0 |
| Low | 0 |
| Total | 0 |

## [QA] Report Card

| Field | Value |
|---|---|
| Status | PASS |
| Summary | 4/4 direct criteria passed |
| Issues beyond spec | 0 |
| Matt upstream read | `vendor/mattpocock-skills/skills/engineering/domain-modeling/SKILL.md` |
