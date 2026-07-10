# DEC-0005: Activation Contract - Entered State Is Disk Facts

> Date: 2026-07-10
> Status: Accepted
> Scope: Activation Layer (Detect → Classify → Enter/Resume → Announce)

## Background

Plugin value equals executed constraints.
If a coding agent never enters yishuship state, hooks, phase gates, and
artifact conventions never fire, and the plugin is effectively dead.

Activation must therefore be:

1. Detectable without LLM judgment alone.
2. Enterable with a single bootstrap command.
3. Observable as durable disk facts, not chat memory.

## Decision

### 1. Entered state = observable disk facts

A session is **entered** only when all of the following are true:

| Fact | Location |
|------|----------|
| `task_id` | `.ship/tasks/<task_id>/` exists |
| `run_state.yaml` | `.ship/tasks/<task_id>/control/run_state.yaml` |
| Announced mode | Agent emits `[yishuship] mode=... phase=... task=...` after enter/resume |

Minimal `run_state.yaml` shape (same root as pm-init / auto-orchestrate):

```yaml
task_id: <id>
active: true
current_phase: <phase>
status: running
updated_at: "YYYY-MM-DDTHH:MM:SSZ"
```

There is **one** state root: `.ship/tasks/<task_id>/`.
Do not invent a second task tree or parallel control plane.

### 2. Delivery intents are default-on; bypass is explicit

| Intent class | Default | Bypass |
|--------------|---------|--------|
| Delivery (feature, fix that needs process, design, implement, test, review, ship) | Must enter state before business source edits | Explicit L0 only |
| Tiny local fix / pure Q&A / unrelated conversation | May stay out of state | Implicit L0 |
| Project opt-out | N/A | `.ship/config.yaml` with `enabled: false` |

L0 bypass must be **stated** when used on a delivery-shaped request:

```text
[yishuship] mode=L0_bypass reason=<one line>
```

Silent skip of delivery process is a contract violation.

### 3. State before business code (unless L0 bypass)

For delivery intents:

```text
Detect enablement
  → Classify (resume | route | enter)
  → Enter or Resume (bootstrap)
  → Announce [yishuship] mode=... phase=... task=...
  → Then edit business source
```

Business source means application/library code the user asked to change.
Editing yishuship control artifacts (`.ship/`, plans, decisions) to establish
state is allowed before announcement completes.

### 4. After enter: State Sense before execute

`bootstrap status` must diagnose project/task state for humans, not only machines:

| Field | Meaning |
|-------|---------|
| `sense_where` | Where we are now |
| `sense_gap` | What is missing |
| `sense_next` | One next skill/action |
| `sense_effect` | What changes after that step |
| `sense_presentation` | How the user verifies the change |
| `sense_preview` | Smallest feel-first slice before full commit |
| `sense_report` | One pasteable Chinese line with all six |

Naked "next step" without effect/presentation/preview is a contract violation.

### 5. Host adapters implement the same contract

| Host surface | Responsibility |
|--------------|----------------|
| SessionStart hook | Inject structured `YISHUSHIP_STATUS` + `YISHUSHIP_STATE_SENSE` from bootstrap `status` |
| Router skill (`use-yishuship`) | Hard rule: enter before business edits; announce; L0 path |
| `scripts/yishuship-bootstrap.sh` | Canonical Detect / Enter / Status |
| PreToolUse / Stop hooks | Optional enforcement; **not** required for contract validity |

Hosts without hooks (plain Codex skills, manual agents) still obey the contract
by calling bootstrap and announcing. Hooks are amplifiers, not the source of truth.

## Enablement detection

yishuship is **enabled** in a repo when any of these exist:

1. `.ship/config.yaml` with `enabled: true` (or absent `enabled` key treated as true if file exists and is not explicitly false)
2. `.ship/enabled` marker file
3. Active `.ship/tasks/*/control/run_state.yaml` (`active: true` or `status: running`)
4. `.ship/ship-auto.local.md`
5. `.ship/pm-state.yaml`

Explicit opt-out:

```yaml
# .ship/config.yaml
enabled: false
```

When `enabled: false` and there is no active task, `next_action` is `bypass_ok`.

## Project config fields

Minimal template (copy to project root as `.ship/config.yaml`):

```yaml
# yishuship project config
enabled: true
```

Optional future fields may extend this file; `enabled` is the only required key
for Activation Layer v1.

## Bootstrap status contract

`scripts/yishuship-bootstrap.sh status` prints machine-readable `key: value` lines:

| Key | Values |
|-----|--------|
| `enabled` | `true` \| `false` |
| `active_task` | task id or `none` |
| `phase` | current phase or `none` |
| `next_action` | `resume` \| `route` \| `idle` \| `bypass_ok` |
| `reason` | short human hint |

`enter [reason]` creates or reuses a task directory and writes `run_state.yaml`
if missing, then prints `task_id: <id>`.

## Consequences

- SessionStart stays small but injects structured status, not only soft prose.
- Agents can resume across sessions from disk without chat history.
- SkillOpt / benchmarks can assert enter-state behavior without host hooks.
- Weak hosts that ignore hooks still have a portable activation path.

## Related

- Router: `skills/use-yishuship/SKILL.md`
- Bootstrap: `scripts/yishuship-bootstrap.sh`
- SessionStart: `scripts/session-start.sh`
- State writers: `scripts/pm-init.sh`, `scripts/auto-orchestrate.sh`
- Ops: `docs/operations/activation.md`
