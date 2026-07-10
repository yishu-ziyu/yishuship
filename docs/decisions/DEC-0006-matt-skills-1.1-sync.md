# DEC-0006: Sync vendored Matt skills to 1.1.0

> Date: 2026-07-10
> Status: Accepted

## Background

yishuship vendors Matt Pocock skills as the engineering standard layer
(`vendor/mattpocock-skills/`). Upstream released **1.1.0** with breaking renames
and new skills. Keeping stale `to-prd` / `to-issues` paths makes runtime
activation lie: phases "read Matt" against files that no longer exist upstream.

## Decision

1. Refresh vendor snapshot to upstream HEAD at sync time
   (`d574778f94cf620fcc8ce741584093bc650a61d3`, package 1.1.0).
2. Map renames everywhere in yishuship (not only docs):

| Old | New |
|-----|-----|
| `to-prd` | `to-spec` |
| `to-issues` / `to-plan` | `to-tickets` |
| `decision-mapping` | `wayfinder` |

3. Embed new skills into phase activation:

| New skill | yishuship use |
|-----------|----------------|
| `research` | pm-intake / design when primary sources required |
| `wayfinder` | multi-session / greenfield-huge; arch-design programs |
| `to-tickets` wide-refactor | refactor / design when mechanical blast radius |

4. Keep yishuship artifact roots (`.ship/tasks`, `CONTEXT.md`, decisions).
   Matt process discipline; yishuship storage contracts.

5. Preserve aliases in `/yishuship:matt` description so users saying `to-prd`
   still resolve to `to-spec`.

## Non-goals

- Do not fork or rewrite upstream SKILL.md bodies.
- Do not promote every Matt skill to a top-level `/yishuship:*` command.
- Do not make `wayfinder` the default entry for every small feature (upstream:
  situational on-ramp, not new main spine).

## Verification

- `python3 benchmarks/test_matt_runtime_activation.py`
- Required upstream paths exist; phase skills reference canonical 1.1 paths.
- Old `to-prd` / `to-issues` directories absent under vendor.

## Revisit when

- Upstream major renames again.
- SkillOpt Matt flow scorer hard-nodes need rename parity.
