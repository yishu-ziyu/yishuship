---
name: arch-design
description: >
  Think through architecture, API/data design, service boundaries, trade-offs,
  and assumptions. Use for system design, ADRs, API plans, and architecture docs;
  then hand off to /yishuship:write-docs. Not visual or implementation planning.
  Use /yishuship:pm-intake for architecture selection; this skill assumes the
  architecture direction is already chosen.
allowed-tools:
  - Read
  - Bash
  - Write
  - Agent
  - AskUserQuestion
  - TodoWrite
---

# Architectural Design

## 入口判断（必读）

**这是详细设计 skill，不是架构选型 skill。** 进入本 skill 前先确认：

- 用户已知架构选型（来自 `pm/01.5-architecture-decision.md` 或用户明示）→ 继续
- 用户还没选定架构（请求含「选架构」「用什么」「X 还是 Y」）→ **退出本 skill**，引导用户走 `/yishuship:pm-intake` Step 1.5

**意图模糊时**，问用户：

> 「你已经定好用哪个架构了吗？如果没有，建议先走 `/yishuship:pm-intake` 做架构选型（Step 1.5），选完再回来做详细设计——避免选错架构导致返工。」

不要在没有架构决策的情况下直接做详细设计——这是 pm-intake 设计的反 drift 机制。

---

## 本 skill 的范围

Think through system design decisions rigorously before writing them down. This skill is about the **thinking** — requirements, components, trade-offs, boundaries. When the design is ready, you MUST invoke `Skill("write-docs")` to write the design document — do not write the doc inline.

## Matt Flow Layer

Before architecture work that affects code structure, read
`../.shared/matt-pocock-standard.md` and
`../../vendor/mattpocock-skills/skills/engineering/codebase-design/SKILL.md`.
When the work is rescuing an existing messy system, also read
`../../vendor/mattpocock-skills/skills/engineering/improve-codebase-architecture/SKILL.md`.
Use Matt's `codebase-design` vocabulary as the shared language for the design:

- `module`: a unit that owns behavior behind an interface.
- `interface`: the small surface other code depends on and tests through.
- `implementation`: the hidden behavior behind that interface.
- `depth`: how much useful behavior the module hides relative to interface size.
- `seam`: a boundary where change, substitution, or testing can happen.
- `adapter`: code that translates across a seam.
- `leverage`: future change made cheaper by the design.
- `locality`: how much of the system must be read or edited to make a change.

This skill turns those concepts into a durable design doc. It does not replace
`/yishuship:pm-intake`; if the product direction or architecture choice is still
unsettled, route back there first.

## Scale to Complexity

Not every decision needs all 5 phases. Match the depth to the decision:

- **Small** (single component, clear constraints) — Phase 1 briefly, Phase 2, Phase 5. Skip deep dive and scaling.
- **Medium** (multi-component, some unknowns) — All 5 phases, but keep each concise.
- **Large** (new system, significant unknowns, cross-team) — All 5 phases in full depth, with diagrams and explicit load estimates.

## Red Flag

**Never:**
- Skip requirements gathering and jump straight to a solution
- Design without understanding existing constraints (tech stack, team, timeline)
- Omit trade-off analysis — every decision has alternatives that were rejected for a reason
- Skip the Boundaries section — it's the core anti-drift mechanism
- Propose a design without verifying assumptions against the actual codebase
- Conflate "what we want" with "what exists" — be explicit about the gap
- Create a seam just because it feels tidy. A seam needs real leverage:
  existing variation, likely near-term variation, or a test boundary that
  materially improves feedback.
- Design shallow modules where every caller still needs to understand the
  implementation details.
- Treat the design doc as finished without naming the public interface and
  test surface for the modules it changes.

## Phase 1: Requirements Gathering

Before designing anything, understand what you're solving.

### Functional Requirements
- What must the system do? List concrete capabilities.
- What are the input/output contracts?
- What user-facing behaviors are required?

### Non-Functional Requirements
- **Latency**: What response times are acceptable? (p50, p99)
- **Throughput**: How many requests/events per second?
- **Availability**: What uptime target? (99.9%? 99.99%?)
- **Consistency**: Strong consistency required, or eventual is acceptable?
- **Data volume**: How much data now? Growth rate?

### Constraints
- Existing tech stack and infrastructure
- Team size and expertise
- Timeline and budget
- Compliance and regulatory requirements
- Backward compatibility requirements

## Phase 2: High-Level Design

Map out the major components and how they interact.

- **Component diagram**: Major services/modules and their responsibilities. Each component should have a single clear purpose. Use ASCII art, mermaid, or a described diagram — the format matters less than clarity.
- **Data flow**: How data moves through the system — request paths, event flows, data pipelines. A sequence diagram helps for complex flows.
- **API contracts**: Key interfaces between components. Define input/output shapes, not implementation.
- **Storage choices**: Which database(s), why. Access patterns determine storage choice, not the other way around.
- **Module depth**: For each important module, name the interface it exposes,
  the behavior it hides, and why that boundary improves leverage or locality.

## Phase 3: Deep Dive

Go deep on the components that matter most.

- **Data model**: Entities, relationships, indexes. Think about access patterns — how will this data be queried?
- **API design**: REST vs GraphQL vs gRPC. Endpoint structure, authentication, rate limiting, versioning strategy.
- **Caching strategy**: What to cache, invalidation approach, TTL. Cache only what's read-heavy and tolerant of staleness.
- **Async and queues**: What needs to be asynchronous? Retry policies, dead-letter queues, idempotency.
- **Error handling**: Failure modes for each component. Fallback strategies, circuit breakers, graceful degradation.

## Phase 4: Scale and Reliability

Design for the load you'll actually face, not hypothetical scale.

- **Load estimation**: Back-of-envelope calculations for storage, bandwidth, compute. Ground these in real numbers.
- **Scaling strategy**: Horizontal vs vertical. Sharding strategy if needed. Read replicas.
- **Failover**: What happens when each component fails? Single points of failure?
- **Monitoring**: Key metrics to track, alerting thresholds, dashboards. What does "healthy" look like?

## Phase 5: Trade-off Analysis

Every design decision has trade-offs. Make them explicit.

For each major decision:
- **What alternatives were considered** (at least 2)
- **Pros and cons of each** (concrete, not vague)
- **Why this choice won** (the deciding factor)
- **What we're giving up** (be honest about costs)
- **Interface cost** (when code structure changes) — what callers must learn,
  what tests can now observe, and what implementation detail stays hidden.

Common trade-off dimensions:
- Consistency vs availability
- Simplicity vs flexibility
- Build vs buy
- Latency vs throughput
- Cost vs performance
- Team familiarity vs best tool for the job

## What to Revisit

Before wrapping up, flag decisions that won't age well:

- **Load-dependent**: "This works at 1k rps but needs rethinking at 10k" — name the threshold.
- **Time-bound**: "We chose X because Y isn't ready yet" — note when to re-evaluate.
- **Assumption-sensitive**: "If we go multi-region, the consistency model breaks" — link to the assumption.

These aren't weaknesses — they're honest engineering. A design that claims to handle everything forever is hiding its assumptions.

## Design Document Output

When the design thinking is complete, the result should be written as a design document. Every design doc needs:

- **Boundaries section** (required) — what this design does NOT cover, what must not change without updating this doc. This is the core anti-drift mechanism.
- **Trade-offs section** (recommended) — the alternatives considered and why this choice won.
- **Assumptions section** (recommended) — what must be true for this design to hold (e.g., "assumes < 10k concurrent users", "assumes single-region deployment"). When assumptions change, the design is stale.
- **Interfaces and test seams** (required when code changes) — the public
  surfaces implementation should build and tests should verify.

When the design thinking is complete, invoke `Skill("write-docs")` to write the design document with category `design`. Do not write the doc inline — the write-docs skill enforces frontmatter, numbering, and index generation.

## Completion Gate

Done means `Skill("write-docs")` has created or updated a managed document under
`docs/design/` and the report card names that path. If the architecture direction
is not chosen, this skill is `BLOCKED` and routes back to `/yishuship:pm-intake`.

## Execution Handoff

After writing the doc via write-docs, output the report card (read `skills/.shared/report-card.md` for the standard format):

```
## [Arch Design] Report Card

| Field | Value |
|-------|-------|
| Status | <DONE / BLOCKED> |
| Summary | <one-line: what was designed and the key decision> |
| Document | <docs/design/...> |

### Metrics
| Metric | Value |
|--------|-------|
| Phases completed | <N>/5 |
| Trade-offs analyzed | <N> |
| Revisit items | <N> |

### Next Steps
1. **Write the doc (required)** — /yishuship:write-docs with category design
2. **Full workflow** — /yishuship:auto to implement the design
3. **Plan implementation** — /yishuship:design to create executable stories
```
