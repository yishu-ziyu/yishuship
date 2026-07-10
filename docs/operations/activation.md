# Activation Layer

How yishuship becomes active in a coding-agent session.

## Why it exists

Plugin value = executed constraints.
If the agent never enters yishuship state, gates and artifacts never run.

Activation is a short loop:

```text
Detect → Classify → Enter/Resume → Announce
```

Contract: `docs/decisions/DEC-0005-activation-contract.md`.

## Detect

```bash
bash scripts/yishuship-bootstrap.sh status
```

Example (active task + State Sense):

```text
enabled: true
active_task: my-feature
phase: review
next_action: resume
reason: active task via run_state
sense_stage: verified_partial
sense_have: input,pm_handoff,plan,e2e
sense_missing: qa
sense_where: 有进行中任务「my-feature」，当前 phase=review，粗阶段=...
sense_gap: 缺：qa
sense_next: /yishuship:review
sense_effect: 在扩大范围前暴露正确性/规格偏差...
sense_presentation: 按严重级别列出的 findings...
sense_preview: 先只扫当前 diff，不出修复 PR...
sense_report: 【现在】... | 【缺什么】... | 【下一步】... | 【做完后】... | 【你怎么确认】... | 【先感受】...
```

State Sense rule: never give a naked next step.
Every suggestion must include effect + presentation + preview.

Enablement markers (any one is enough, unless config sets `enabled: false`):

- `.ship/config.yaml` (`enabled: true`)
- `.ship/enabled`
- active `.ship/tasks/*/control/run_state.yaml`
- `.ship/ship-auto.local.md`
- `.ship/pm-state.yaml`

## Classify (`next_action`)

| Value | Meaning |
|-------|---------|
| `resume` | Active task on disk - continue it first |
| `route` | Enabled, no active task - run `/yishuship:use-yishuship` then enter |
| `idle` | Not enabled in this repo |
| `bypass_ok` | Explicit project opt-out (`enabled: false`) |

## Enter / Resume

```bash
bash scripts/yishuship-bootstrap.sh enter "short reason"
```

- Reuses the active task when present.
- Otherwise creates `.ship/tasks/<task_id>/` and writes
  `control/run_state.yaml` if missing.
- Prints `task_id: ...` for the agent to announce.

## Announce

After enter or resume, the agent must emit:

```text
[yishuship] mode=<pm|design|dev|...> phase=<phase> task=<task_id>
```

L0 bypass (tiny fix / pure Q&A, or explicit skip of delivery process):

```text
[yishuship] mode=L0_bypass reason=<one line>
```

## SessionStart

`scripts/session-start.sh` calls bootstrap `status` and injects a compact
`YISHUSHIP_STATUS` block so the host agent sees structured facts, not only
soft routing prose.

## Project config

```yaml
# .ship/config.yaml
enabled: true
```

Set `enabled: false` only when the project intentionally opts out of yishuship.
