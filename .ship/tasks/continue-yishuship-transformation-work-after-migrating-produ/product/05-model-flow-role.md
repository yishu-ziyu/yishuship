# Model, Flow, and Role

## Business Data Model

The main objects are Task, Product Lifecycle State File, PM Handoff, Phase State, Artifact Integrity Manifest, Guardrail, Verifier, Benchmark, and Handoff Evidence.
A Task lives under `.ship/tasks/<task_id>/`.
The Product Lifecycle State File is `product/00-product-type.json` for new tasks, with legacy YAML accepted during migration.
The PM Handoff is the artifact set that allows engineering phases to begin.
The Phase State is `.ship/ship-auto.local.md` plus task-level `control/run_state.yaml`.
The Artifact Integrity Manifest is `.ship/.checksums`.
A Guardrail is a hook-facing script that blocks unsafe tool behavior.
A Benchmark is a repeatable test that verifies workflow behavior from the outside.

## Object Relationships

A Task owns product, delivery, plan, control, e2e, qa, and growth artifacts.
The orchestrator owns `.ship/ship-auto.local.md` and updates task-level run state.
The PM Handoff depends on product artifacts and creates the safe seam for design and development.
The Artifact Integrity Manifest references selected `.ship` control files by repo-relative path and hash.
Guardrails use the current Phase State and PM Handoff to decide whether a subagent tool call is allowed.
Benchmarks exercise scripts and hooks through representative JSON input, not by inspecting implementation internals only.

## Workflow

The workflow remains staged: pm_intake, design, dev, e2e, review, qa, refactor, handoff.
This slice strengthens the transitions between those stages.
PM intake must complete before design.
Design and development must receive acceptance criteria from plan and delivery artifacts.
Subagent source writes must not happen before PM handoff.
Checksum validation must run before phase transitions and guarded `.ship` writes.
Test evidence must be captured before claiming the hardening slice is done.

## Roles and Handoffs

The user supplies intent and decides hard-to-reverse product trade-offs only when code and local context cannot answer them.
The orchestrator owns phase state and phase transitions.
The PM intake skill owns product intent and engineering handoff artifacts.
The design and dev skills own implementation planning and changes after the PM gate.
The phase guardrail owns enforcement against unsafe subagent writes.
The stop gate owns final session safety checks.
The benchmark suite owns regression evidence.
