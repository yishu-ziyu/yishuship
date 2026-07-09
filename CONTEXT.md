# yishuship Context

This file records domain language for yishuship workflow work.
It is a glossary, not an implementation spec.

## Terms

### Product lifecycle state file

The product lifecycle state file is the first structured PM artifact for a task.
Its canonical new format is `product/00-product-type.json`.
Legacy `product/00-product-type.yaml` may be accepted during migration, but new tasks should write JSON.

### PM handoff

A PM handoff is the minimum product-to-engineering artifact set that makes source code changes safe.
It includes product type, strategy, problem and solution, PRD, technical plan, engineering design spec, and engineering-facing acceptance criteria.

### Artifact integrity manifest

The artifact integrity manifest is `.ship/.checksums`.
It stores SHA-256 hashes for selected `.ship` control files that agents read and write across phases.
It protects workflow state from silent truncation or accidental mutation.

### Long-horizon E2E safety net

The long-horizon E2E safety net is a benchmark suite that exercises multi-phase workflow behavior across PM gates, guardrails, stop gates, checksum validation, and cross-session resume.
It is not a UI E2E test.

### Subagent bypass

A subagent bypass is any path where an agent writes source code without completing the PM handoff first.
yishuship treats this as a workflow correctness bug.
