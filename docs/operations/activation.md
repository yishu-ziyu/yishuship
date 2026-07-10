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

Example (active task):

```text
enabled: true
active_task: my-feature
phase: dev
next_action: resume
reason: active task via run_state
```

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
