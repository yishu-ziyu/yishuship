# Report Card Format

All Ship skills output a structured report card at the end of execution.
This format is consistent across all skills so users always know where to look.

## Template

```markdown
## [Phase] Report Card

| Field | Value |
|-------|-------|
| Status | <DONE / DONE_WITH_CONCERNS / FINDINGS / BLOCKED / SKIP> |
| Summary | <one-line description of what happened> |
| Matt upstream read | <comma-separated vendor paths opened this phase, or none + why> |

### Metrics
| Metric | Value |
|--------|-------|
| <phase-specific metric> | <value> |

### Artifacts
| File | Purpose |
|------|---------|
| <path> | <what it is> |
```

When the phase skill lists required Matt `SKILL.md` paths, **Matt upstream read**
must not be empty on DONE. Writing the path without opening the file is a
contract violation.

Always include Next Steps — the orchestrator reads the report card the same
way a human does. No separate auto/standalone output formats.

```markdown
### Next Steps
1. **Recommended** — /yishuship:<next-skill>
2. **Alternative** — /yishuship:<other-skill>
3. **Other** — <description>
```

## Phase-Specific Metrics

| Phase | Metrics |
|-------|---------|
| Auto | Phases completed, Review fix rounds, QA fix rounds, E2E fix rounds, Total agents dispatched |
| Design | Stories count, Files traced, Divergences resolved, Drill steps CLEAR |
| Dev | Stories completed, Waves, Concerns, Test result |
| Review | P1/P2/P3 counts (or "Clean") |
| QA | Criteria passed/total, Issues beyond spec |
| E2E | Framework (pre-existing/scaffolded), Tests added, Suite pass rate, Regressions |
| Refactor | Smells fixed, Lines before/after, Functions extracted, Dead code deleted |
| Handoff | PR URL, Check status, Fix rounds |
| Arch Design | Phases completed, Trade-offs analyzed, Revisit items |
| Write Docs | Docs created, Docs updated, Index regenerated |

## Status Values

| Status | Meaning |
|--------|---------|
| DONE | Phase goal met, no issues |
| DONE_WITH_CONCERNS | Goal met but residual concerns logged |
| FINDINGS | Goal met but issues found that need fixing (review/QA) |
| BLOCKED | Cannot proceed without external input |
| SKIP | Phase not applicable |
