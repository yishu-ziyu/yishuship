# Unknown Gate

Canonical rule for **unknown → research first** across yishuship.

Not a product lifecycle phase (see `product-lifecycle-21.md`).
Not full pm-intake research by default.
This file only fixes: **what counts as unknown, and what to do before writing as if you know**.

```text
No citable evidence → Unknown
Unknown → research first (or label assumption / ask user)
Confidence is not evidence
```

## Why this exists

Agents sound certain while inventing.
yishuship already researches at pm-intake for product decisions.
This gate covers **mid-flight** work: design, code, APIs, repo facts, runtime behavior.

## Definition: Unknown

An assertion is **unknown** if this turn has **no citable evidence** for it.

Citable evidence means one of:

- User text in this conversation that states the fact
- A file path you **read this turn** (or earlier in this turn's tool trace)
- An official URL / primary source you **opened this turn**
- Command / test output from this turn
- A project artifact (spec, DEC, `product/*`) that still applies and you can point to

**Model weights alone are not evidence.**
"Usually / generally / I recall / should be fine" without a cite → unknown.

### Types (A–F) — any match means unknown

| Code | Type | Trigger |
|------|------|---------|
| A | Outside world | Claim about current products, prices, news, laws, market — no primary source this turn |
| B | API / library contract | Params, defaults, version behavior — official docs or source not opened this turn |
| C | This repo | Paths, existing behavior, ownership — not Read/Grep'd this turn |
| D | User intent / scope | Acceptance, tradeoffs, must/must-not — not stated; multiple costly interpretations |
| E | Runtime | Live status, auth, real HTTP/DB behavior — not observed this turn |
| F | Untested critical path | Happy path only; no check on the failure that would matter |

### Known (may proceed)

Evidence exists **this turn** and you can name it (path, URL, or output snippet).

## Procedure

When about to assert, design, or edit based on something that may be unknown:

1. **Scan** — does the next action rely on A–F without a cite?
2. **If yes → Gate open (must research or stop)**
   - Pick the **smallest** research action that produces a cite
   - Then proceed with the cite in mind
3. **If research fails** — do **not** invent certainty:
   - Label `ASSUMPTION: ...` with risk, or
   - Ask the user one tight question, or
   - Mark phase `BLOCKED` with what is missing
4. **Never** treat fluency or confidence as a substitute for a cite

### Research actions by type

| Type | Prefer | Examples |
|------|--------|----------|
| A | Live primary sources | AnySearch → official site / first-party post; not random blogs as sole proof |
| B | Official docs or library source | Vendor docs, package types, upstream README |
| C | Repo tools | Read, Grep, list, blame when needed |
| D | User | One clarifying question; or pm-intake if product-shaped |
| E | Observe | Run app, curl, test, reproduce |
| F | Prove | Minimal test, manual path, or explicit out-of-scope |

### Depth

| Situation | Depth |
|-----------|--------|
| Mid design/dev, single API or file fact | **Light**: one search or one doc/read, cite, continue |
| Product "should we build / who for / competitors" | **pm-intake research** (`product/02-research.md`), not this light gate alone |
| Hard bug / unknown system | Diagnosis loop + primary sources; Matt `research` skill when reading is the job |

## Forbidden

- Writing production logic on uncited B/C/E claims
- Filling PRD/spec numbers or API shapes from memory only
- Saying "done" while critical path is type F with no check
- Silent skip of the gate on delivery work

## Allowed without full research

- Pure restatement of user-provided facts
- Pure formatting / rename with no new claims
- Explicit user order: "don't research, just draft" (then label assumptions)

## Self-check (before edit or "done")

```text
[ ] Every non-trivial claim I rely on has a cite (path / URL / output)
[ ] No "usually / I recall" without a source opened this turn
[ ] Unknowns either researched, labeled ASSUMPTION, asked, or BLOCKED
```

If any box fails → open the gate; do not ship the step.

## Relationship to other shared files

| File | Role |
|------|------|
| `product-lifecycle-21.md` | Product research stages |
| `execution-model.md` | Order / parallel / failure loops |
| `matt-pocock-standard.md` | Engineering skill standards; use Matt `research` for primary-source investigations |
| **This file** | Cross-cutting unknown → research first |
