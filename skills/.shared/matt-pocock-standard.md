# Matt Pocock Engineering Flow Standard

This repository vendors Matt Pocock's skills at `vendor/mattpocock-skills/`.
From this shared file, the same tree is `../../vendor/mattpocock-skills/`.
Treat those files as the upstream standard layer for engineering workflow
quality. Do not rewrite their contents into yishuship skills; reference them
and preserve their meaning.

**Vendored line:** package `1.1.0`, revision pinned in `vendor/README.md`.

## Naming aliases (1.1.0)

| Legacy name (docs / habit) | Canonical upstream path |
|----------------------------|-------------------------|
| `to-prd` | `skills/engineering/to-spec/SKILL.md` |
| `to-issues`, `to-plan` | `skills/engineering/to-tickets/SKILL.md` |
| `decision-mapping` | `skills/engineering/wayfinder/SKILL.md` |

Always open the **canonical** path. If the user says the legacy name, map it
and say so once.

## Runtime Activation

When a yishuship phase maps to a Matt skill, the phase must **open and read**
the upstream `SKILL.md` before executing that part of the workflow. Listing a
path in this file is not enough; the agent must actually load the file.

Proof of use (required for DONE on phases that declare Matt deps):

1. Open each required path with the Read tool (or equivalent).
2. Record paths in the phase report card field `Matt upstream read`.
3. For `pm-intake`, also write `control/matt-upstream.md` in the task dir.

This is the difference between "inspired by Matt" and "using Matt".

Use these runtime activations:

| yishuship phase | Must read upstream Matt skills |
|---|---|
| `use-yishuship` | `ask-matt` when routing is non-trivial; `wayfinder` when work is multi-session / greenfield-huge |
| `matt` | selected upstream skill only (see `/yishuship:matt` table) |
| `pm-intake` | `grill-with-docs`, `grilling`, `domain-modeling`, `to-spec`, `prototype` when needed; `research` when primary-source investigation is required before product claims |
| `design` | `grill-with-docs` when alignment is unresolved; `prototype` for runnable design questions; `to-tickets`; `codebase-design` when module boundaries matter; `research` when design depends on external/primary docs |
| `dev` | `implement`, `tdd`, `diagnosing-bugs` for bug/perf fixes |
| `e2e` | `tdd` for behavior-through-public-seam discipline |
| `review` | `code-review` (includes Fowler smell baseline on Standards axis) |
| `refactor` | `improve-codebase-architecture`, `codebase-design`; `to-tickets` wide-refactor rules when blast radius is whole-codebase mechanical |
| `arch-design` | `codebase-design`; `improve-codebase-architecture` when rescuing existing systems; `wayfinder` when the architecture program spans many sessions |
| `handoff` | `handoff`; `resolving-merge-conflicts` when merge/rebase conflicts appear |
| `write-docs` | `domain-modeling` for shared language docs; `handoff` for cross-session docs |
| `qa` | `domain-modeling` when verifying domain language in UI/copy; otherwise phase-local evidence |

Load only the upstream skills relevant to the current route. If a yishuship
skill names an upstream file as required, read it completely; do not rely on
this summary as a substitute.

Canonical upstream paths (1.1.0):

- Flow router: `vendor/mattpocock-skills/skills/engineering/ask-matt/SKILL.md`
- Huge multi-session map: `vendor/mattpocock-skills/skills/engineering/wayfinder/SKILL.md`
- Alignment: `vendor/mattpocock-skills/skills/productivity/grilling/SKILL.md`
- Stateful alignment + docs: `vendor/mattpocock-skills/skills/engineering/grill-with-docs/SKILL.md`
- Domain model: `vendor/mattpocock-skills/skills/engineering/domain-modeling/SKILL.md`
- Spec (was to-prd): `vendor/mattpocock-skills/skills/engineering/to-spec/SKILL.md`
- Tickets / vertical slices (was to-issues): `vendor/mattpocock-skills/skills/engineering/to-tickets/SKILL.md`
- Primary-source research: `vendor/mattpocock-skills/skills/engineering/research/SKILL.md`
- Prototype branch: `vendor/mattpocock-skills/skills/engineering/prototype/SKILL.md`
- Implementation: `vendor/mattpocock-skills/skills/engineering/implement/SKILL.md`
- TDD discipline: `vendor/mattpocock-skills/skills/engineering/tdd/SKILL.md`
- Bug diagnosis: `vendor/mattpocock-skills/skills/engineering/diagnosing-bugs/SKILL.md`
- Codebase design vocabulary: `vendor/mattpocock-skills/skills/engineering/codebase-design/SKILL.md`
- Architecture health: `vendor/mattpocock-skills/skills/engineering/improve-codebase-architecture/SKILL.md`
- Two-axis review: `vendor/mattpocock-skills/skills/engineering/code-review/SKILL.md`
- Session handoff: `vendor/mattpocock-skills/skills/productivity/handoff/SKILL.md`
- Skill quality: `vendor/mattpocock-skills/skills/productivity/writing-great-skills/SKILL.md`
- Merge conflict resolution: `vendor/mattpocock-skills/skills/engineering/resolving-merge-conflicts/SKILL.md`

## Architecture

Matt's stable architecture has two layers:

1. **User-invoked orchestrators** choose the path and own stateful workflow.
2. **Model-invoked disciplines** supply reusable engineering judgment.

yishuship mirrors this as:

- `/yishuship:*` skills are orchestrators.
- This shared file and vendored Matt skills are standards/discipline layers.
- Do not expose every vendored skill as a yishuship command until a concrete
  route earns that surface area.

## Main Flow Mapping (1.1.0)

Use this mapping for non-trivial product or engineering work:

| Matt flow | yishuship phase | Required adaptation |
|---|---|---|
| `/wayfinder` | multi-session product/eng programs | When one session cannot hold the map: investigation tickets first, then normal flow. Not default for every small feature. |
| `/grill-with-docs` | `pm-intake`, `design` | One decision question at a time; facts from codebase vs decisions from human; confirmation gate before enacting; update `CONTEXT.md` and decisions. |
| `/research` | `pm-intake`, `design` | Background primary-source dig; cite into repo notes; do not invent API/docs claims. |
| `/prototype` | `pm-intake`, `design` | Model-invoked OK; throwaway code answers a design question; keep the answer, not the demo. |
| `/to-spec` (was to-prd) | `pm-intake` | Synthesize product artifacts + engineering-facing acceptance; confirm test seams before handoff. |
| `/to-tickets` (was to-issues) | `design`, `dev` | Tracer-bullet vertical slices with blocking edges; wide-refactor expand-contract when blast radius is mechanical and codebase-wide. |
| `/implement` + `/tdd` | `dev`, `e2e` | One vertical slice; red before green at agreed seams. |
| `/code-review` | `review`, `handoff` | Standards + Spec axes separate; Standards includes Fowler smell baseline (judgement, not hard fail unless repo standard says so). |
| `/handoff` | `handoff`, cross-session auto | Do not duplicate artifacts already on disk. |

Main Matt spine (upstream):

```text
grill-with-docs → to-spec → to-tickets → implement(+tdd) → code-review
```

Situational on-ramps: `wayfinder` (too big), `diagnosing-bugs` (broken), `triage` (incoming queue), `research` (primary sources).

## On-Ramps

| Situation | Matt standard | yishuship route |
|---|---|---|
| Raw incoming issue/request | `triage` | `pm-intake` or local issue workflow |
| Hard bug/perf regression | `diagnosing-bugs` | `review` to find; `dev` fix from tight feedback loop |
| Codebase entropy | `improve-codebase-architecture` + `codebase-design` | `refactor` or `arch-design` |
| Greenfield / multi-session program | `wayfinder` | `pm-intake` + `wayfinder` map before full auto |
| External/API truth unknown | `research` | Before hard product or design claims |

## Non-Negotiables

- **Misalignment first**: do not build when the product/user intent is unresolved.
- **Facts vs decisions** (grilling 1.1): look up facts in the codebase; put decisions to the human.
- **Shared language**: use `CONTEXT.md` for domain terms; `docs/decisions/` for hard-to-reverse trade-offs.
- **One question at a time** when user input is required.
- **Prototype only to answer**: preserve the decision, not the demo.
- **Vertical slices**: independently verifiable; use wide-refactor rules when vertical is impossible.
- **Tight feedback loop** for debugging.
- **Deep modules** vocabulary from codebase-design.
- **Two-axis review**: Standards and Spec separate; then aggregate.

## License

Matt Pocock's vendored skills are MIT licensed. Keep
`vendor/mattpocock-skills/LICENSE` with the vendored source.
