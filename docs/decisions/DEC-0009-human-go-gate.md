# DEC-0009: Human Go gate after PM intake

> Date: 2026-07-14
> Status: Accepted

## Decision

1. Product handoff minimum includes `product/00c-go-decision.md` with:
   - `## Decision` → Go / No-Go / Shrink
   - `## Human approval` with `status: pending | approved | rejected`
2. Under `/yishuship:auto` with `require_human_go: true` (default on init):
   - `pm_intake:success` does **not** auto-dispatch design while approval is pending
   - Orchestrator emits `ACTION:await_human` / phase `await_human_go`
   - User approves via edit (`status: approved`) or
     `bash scripts/auto-orchestrate.sh approve_go`
   - Decision No-Go ends the auto spine (`ACTION:done`, phase `stopped_nogo`)
3. Agent may draft Decision and budget; agent must not forge `status: approved`
   unless the user explicitly said Go in the same turn (standalone pm-intake only).
4. CI/benchmarks may set `require_human_go: false` or
   `YISHUSHIP_REQUIRE_HUMAN_GO=0`, but still must ship a valid 00c file.

## Why

- Super-individual / OPC delivery: only the human is the board. Auto was
  advancing `pm_intake → design` without a human commit gate.
- 玄米-style「立项」maps to this gate, not to a new free-form router.
- Artifact-first keeps the gate auditable; `await_human` makes it hard-stop.

## Consequences

- `validate_pm_minimum`, `pm-gate.sh`, and fixtures require 00c.
- Auto skill must handle `ACTION:await_human` and not invent approval.
- Full dynamic routing by external process tables is **out of scope** (see
  `docs/operations/entry-and-flow-mapping.md`).

## Related

- `skills/.shared/product-lifecycle-21.md` Engineering Gate
- `scripts/auto-orchestrate.sh` (`advance_after_pm_intake`, `approve_go`)
- `scripts/pm-gate.sh`
