# yishuship Execution Model

Canonical rule for **how work runs** inside yishuship.

Not a product lifecycle (see `product-lifecycle-21.md`).
Not Matt's skill bodies (see `matt-pocock-standard.md`).
This file only fixes: **order, parallel, and failure loops**.

```text
Layer 1  Stage dependencies   serial when required
Layer 2  Intra-stage work     parallel when safe
Layer 3  Failure              loop back, do not fake forward
```

## Layer 1 - Stage dependencies (serial where needed)

Default auto spine (dependency order, not mandatory full run):

```text
pm_intake → design → dev → e2e → review → qa → [refactor] → handoff
```

| Downstream | Upstream required (minimum idea) |
|------------|-----------------------------------|
| design | product handoff enough to plan (type, problem, PRD/spec, tech plan, design-spec) |
| dev | executable spec + plan with slices |
| e2e | user-visible behavior exists to lock |
| review | code/diff exists |
| qa | app can start |
| handoff | something worth shipping |

Rules:

1. **Do not start a stage whose upstream artifacts are missing** (gate / validate).
2. **Skip stages** that do not apply (L0 tiny fix, docs-only, user opt-out of full auto).
3. **Never invent parallel across stages** that share a write-set without isolation
   (e.g. do not parallel pm_intake writing product/* with dev editing app code
   on the same claim of "done").

Allowed non-linear moves:

- Jump to a single stage when the user is already mid-pipeline and state says so.
- Multi-session programs: use Matt `wayfinder` to map investigation tickets first,
  then re-enter the spine.

## Layer 2 - Intra-stage parallel (when safe)

Parallel only when **all** hold:

1. No shared write conflicts (different files / clear ownership).
2. Independent acceptance (each unit can pass/fail alone).
3. Results merge through a defined host step (diff, wave merge, report card).

| Stage | Parallel pattern (already preferred) |
|-------|--------------------------------------|
| design | host investigation ∥ peer investigation; then serial diff |
| dev | stories in the same wave in parallel if file DAG allows |
| review | Standards axis and Spec axis may be split across peers; host merges |
| research (Matt) | background primary-source dig while host continues alignment |
| auto | one phase at a time at orchestrator level; parallelism stays inside the phase skill |

Forbidden by default:

- Two agents editing the same file without worktree/partition.
- "Parallel design + implement" as default for product features.
- Fan-out without a merge/verify step.

## Layer 3 - Failure loops (retry, do not lie)

| Failure | Loop |
|---------|------|
| design peer/drill blocked | revise plan → re-drill (bounded) |
| dev story FAIL review | implementer fixes → peer re-review (max rounds in skill) |
| e2e / review / qa fail under auto | `*_fix` → dev-fix → re-run failing phase |
| stage retry exhausted | `escalate` / BLOCKED with evidence, not silent continue |

Rules:

1. **Red signal must be re-checked** after fix (re-run the failing gate).
2. **Same implementer fixes** when context matters (dev skill rule).
3. **Max retries are real** (auto: per-phase counters; then escalate).
4. **Do not mark phase complete** if validate_artifacts fails.

## How agents should announce

When choosing a route or phase plan, state:

```text
[execution]
  stage: <name>
  dependency: ok | blocked(<missing>)
  parallel: none | <what runs in parallel>
  loop: none | on-fail → <fix path>
```

## Relation to other files

| File | Owns |
|------|------|
| `execution-model.md` (this) | order / parallel / loops |
| `product-lifecycle-21.md` | product checkpoints |
| `matt-pocock-standard.md` | which Matt SKILL.md to read |
| `runtime-resolution.md` | host vs peer dispatch plumbing |
| `auto-orchestrate.sh` | mechanical phase machine + retries |

## Non-goals

- Replacing Matt skill text.
- Building a general multi-agent OS (Claude dynamic workflows / teams).
- Unbounded self-improving loops without human escalate.
