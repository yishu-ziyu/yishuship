# DEC-0008: Lifecycle spiral timing + multi-agent cross-review

> Date: 2026-07-10
> Status: Accepted

## Decision

1. Treat the 21 checkpoints as a **spiral lifecycle map**, not a pre-code waterfall.
   Each checkpoint has timing: `pre_cycle` | `in_cycle` | `post_cycle` | `continuous`.
2. One engineering pass completes only the **pre_cycle / in_cycle** slice needed
   for that cycle. Points 19–20 (ops, learning) close the loop and may re-open
   earlier checkpoints for the next cycle.
3. **Multi-agent cross-review** of product **inputs and outputs** is required on
   full-scope pm-intake (and already required patterns continue for design/dev).

Canonical text: `skills/.shared/product-lifecycle-21.md`
(sections Checkpoint timing, Multi-agent cross-review).

## Why

- User and protocol intent: super-individual coverage without fake "all 21 done
  before code".
- Continuous discovery practice: dual-track discovery/delivery; validate risks;
  cross-functional challenge (see sources linked in the protocol).
- Single-agent self-approval produces hollow docs; peer review of inputs and
  outputs is the minimum independence bar.

## Consequences

- Checklist may record `when` per checkpoint.
- full pm-intake DONE requires `control/peer-review.md` resolution.
- growth/learn should name next-cycle checkpoint re-opens.

## Non-goals

- Running all 21 deeply every cycle.
- Replacing human product judgment with peer agents alone.
