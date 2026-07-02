# Matt Pocock Engineering Flow Standard

This repository vendors Matt Pocock's skills at `vendor/mattpocock-skills/`.
From this shared file, the same tree is `../../vendor/mattpocock-skills/`.
Treat those files as the upstream standard layer for engineering workflow
quality. Do not rewrite their contents into yishuship skills; reference them
and preserve their meaning.

## Runtime Activation

When a yishuship phase maps to a Matt skill, the phase must read the upstream
`SKILL.md` before executing that part of the workflow. This is the difference
between "inspired by Matt" and "using Matt".

Use these runtime activations:

| yishuship phase | Must read upstream Matt skills |
|---|---|
| `use-yishuship` | `ask-matt` when routing is non-trivial |
| `pm-intake` | `grill-with-docs`, `grilling`, `domain-modeling`, `to-prd`, `prototype` when needed |
| `design` | `grill-with-docs` when alignment is unresolved; `prototype` for runnable design questions; `to-issues`; `codebase-design` when module boundaries matter |
| `dev` | `implement`, `tdd`, `diagnosing-bugs` for bug/perf fixes |
| `e2e` | `tdd` for behavior-through-public-seam discipline |
| `review` | `code-review` |
| `refactor` | `improve-codebase-architecture`, `codebase-design` |
| `arch-design` | `codebase-design`; `improve-codebase-architecture` when rescuing existing systems |
| `handoff` | `handoff`; `resolving-merge-conflicts` when merge/rebase conflicts appear |
| `write-docs` | `domain-modeling` for shared language docs; `handoff` for cross-session docs |

Load only the upstream skills relevant to the current route. If a yishuship
skill names an upstream file as required, read it completely; do not rely on
this summary as a substitute.

Canonical upstream paths:

- Flow router: `vendor/mattpocock-skills/skills/engineering/ask-matt/SKILL.md`
- Alignment: `vendor/mattpocock-skills/skills/productivity/grilling/SKILL.md`
- Stateful alignment + docs: `vendor/mattpocock-skills/skills/engineering/grill-with-docs/SKILL.md`
- Domain model: `vendor/mattpocock-skills/skills/engineering/domain-modeling/SKILL.md`
- PRD: `vendor/mattpocock-skills/skills/engineering/to-prd/SKILL.md`
- Vertical slices: `vendor/mattpocock-skills/skills/engineering/to-issues/SKILL.md`
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

## Main Flow Mapping

Use this mapping for non-trivial product or engineering work:

| Matt flow | yishuship phase | Required adaptation |
|---|---|---|
| `/grill-with-docs` | `pm-intake`, `design` | Ask one decision question at a time when alignment is incomplete; update `CONTEXT.md` and decisions inline when terms or trade-offs crystallize. |
| `/prototype` branch | `pm-intake`, `design` | If a question cannot be settled in conversation, build a throwaway prototype, keep only the answer, and delete or absorb the code. |
| `/to-prd` | `pm-intake` | Synthesize product artifacts and PRD from current context; do not re-interview if the conversation already contains the answer. Confirm test seams before engineering handoff. |
| `/to-issues` | `design`, `dev` | Break plans into tracer-bullet vertical slices, not horizontal layers. Each slice must be independently demoable/verifiable. |
| `/implement` + `/tdd` | `dev`, `e2e` | Implement one vertical slice at a time through agreed seams; red before green; expected values come from spec or known-good examples. |
| `/code-review` | `review`, `handoff` | Keep Standards and Spec axes separate. Do not let one axis mask the other. |
| `/handoff` | `handoff`, cross-session auto runs | Use handoff to cross context windows; do not duplicate artifacts already on disk. |

## On-Ramps

| Situation | Matt standard | yishuship route |
|---|---|---|
| Raw incoming issue/request | `triage` | `pm-intake` or local issue workflow, with ready-for-agent brief semantics. |
| Hard bug/perf regression | `diagnosing-bugs` | `review` only for finding; `dev` fix must start from a tight feedback loop. |
| Codebase entropy | `improve-codebase-architecture` + `codebase-design` | `refactor` or `arch-design`, using deep-module vocabulary. |

## Non-Negotiables

- **Misalignment first**: do not build when the product/user intent is unresolved.
- **Shared language**: use `CONTEXT.md` for domain terms; update it when a term is resolved. Use `docs/decisions/` for hard-to-reverse trade-offs.
- **One question at a time**: if user input is needed, ask the next blocking decision only.
- **Prototype only to answer**: prototype code is throwaway; preserve the decision, not the demo.
- **Vertical slices**: every implementation slice crosses the stack enough to be independently verified.
- **Tight feedback loop**: debugging and fixes need one command or script that can go red on the actual issue.
- **Deep modules**: prefer small interfaces hiding meaningful behavior; use module/interface/depth/seam/adapter/leverage/locality exactly.
- **Two-axis review**: Standards and Spec are separate reports; aggregate only after both are visible.

## License

Matt Pocock's vendored skills are MIT licensed. Keep
`vendor/mattpocock-skills/LICENSE` with the vendored source.
