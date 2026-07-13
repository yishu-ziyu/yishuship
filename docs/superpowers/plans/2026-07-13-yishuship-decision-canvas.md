# Yishuship Decision Canvas Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a native yishuship decision canvas that projects real repository facts, lets users approve proposals, and gives Codex/Claude Code one durable, evidence-gated execution queue.

**Architecture:** Build one dependency-light local service around an append-only `.ship/decision-canvas/events.jsonl` log. A pure reducer owns proposal/decision/execution semantics; a projector derives factual graph nodes from Git and `.ship`; an HTTP/SSE server is the only writer; a static browser canvas is the user authority surface; a small MCP adapter exposes only Agent-safe commands.

**Tech Stack:** Node.js 22 built-ins (`node:http`, `node:fs`, `node:crypto`, `node:child_process`, `node:test`), static HTML/CSS/JavaScript, Bash host hooks, Playwright as a development-only browser test dependency, existing Python `unittest` activation tests.

## Global Constraints

- Do not begin business-source implementation while the existing yishuship task `continue-yishuship-transformation-work-after-migrating-produ` remains active in `review`; finish its Review → QA → Handoff chain first, then enter a fresh decision-canvas task.
- Runtime must not depend on Canvasight, React, XYFlow, a database, or another plugin. Canvasight is reference material only.
- The browser is the only authority allowed to revise, reject, approve, or supersede a proposal. MCP must not expose those commands.
- Git, tests, and existing `.ship/tasks/` artifacts remain factual authorities. The canvas stores references and summaries, never a second copy of source code.
- Every mutation carries an opaque `base_revision`. Stale writes return HTTP `409 revision_conflict` and never append an event.
- The service binds only `127.0.0.1`, authorizes one canonical project root, and requires a per-start bearer token.
- Completing an execution requires at least one existing evidence reference. No evidence means `needs_verification`, never `completed`.
- Approved decisions do not interrupt an Agent. They become claimable only at the Agent's next safe boundary.
- Keep runtime dependency-free. Playwright is development-only and must not be required when a user opens the canvas.
- Preserve the user's existing untracked `.superpowers/` prototype directory; do not stage or delete it.

---

## File Map

**Create**

- `package.json` — local test scripts and the development-only Playwright dependency.
- `package-lock.json` — reproducible browser-test toolchain.
- `playwright.config.mjs` — one Chromium project for the browser decision loop.
- `.mcp.json` — register the native `yishuship-decision-canvas` MCP adapter.
- `decision-canvas/protocol.mjs` — event schema, reducer, command validation, queue semantics.
- `decision-canvas/store.mjs` — JSONL replay, fsync append, corruption handling, project lease.
- `decision-canvas/projector.mjs` — Git/`.ship` fact projection and graph construction.
- `decision-canvas/service.mjs` — localhost HTTP API, SSE stream, static files, authorization.
- `decision-canvas/mcp.mjs` — stdio JSON-RPC/MCP adapter with four Agent-safe tools.
- `decision-canvas/web/index.html` — canvas shell and accessible inspector/form markup.
- `decision-canvas/web/app.js` — spatial graph, SSE reconciliation, real commands.
- `decision-canvas/web/styles.css` — visual system, nodes, edges, focus and connection states.
- `scripts/decision-canvas.mjs` — `start|serve|status|stop|open|pending` CLI.
- `scripts/decision-boundary.sh` — non-blocking pending-decision hint for host boundaries.
- `skills/canvas/SKILL.md` — `/yishuship:canvas` entry point.
- `tests/decision-canvas/helpers.mjs` — temporary Git project and service test helpers.
- `tests/decision-canvas/protocol.test.mjs` — reducer, revision, claim and evidence tests.
- `tests/decision-canvas/store.test.mjs` — persistence, lock, restart and corruption tests.
- `tests/decision-canvas/projector.test.mjs` — real-object fact graph tests.
- `tests/decision-canvas/service.test.mjs` — auth, HTTP commands, SSE and stale-write tests.
- `tests/decision-canvas/mcp.test.mjs` — initialize/tools/list/tools/call contract tests.
- `tests/decision-canvas/browser.spec.mjs` — proposal → approval → claim → evidence completion E2E.
- `docs/operations/yishuship-decision-canvas.md` — operator and recovery guide.

**Modify**

- `.gitignore` — ignore Playwright artifacts and local Node installation output.
- `scripts/session-start.sh` — surface durable pending decisions without starting the service.
- `scripts/auto-orchestrate.sh` — print a pending-decision hint at phase dispatch boundaries.
- `hooks/hooks.json` — run the boundary hint at Claude Stop.
- `hooks/codex-hooks.json` — run the same boundary hint at Codex Stop.
- `skills/use-yishuship/SKILL.md` — route “open/show/decide on canvas” to `/yishuship:canvas`.
- `skills/.shared/runtime-resolution.md` — document the shared decision protocol across hosts.
- `AGENTS.md` — add the fifteenth skill and its validation commands.
- `README.md` — explain the decision loop, command, architecture, and runtime boundary.
- `.claude-plugin/plugin.json` — bump to `0.2.0` and add decision-canvas keywords.
- `.claude-plugin/marketplace.json` — keep marketplace version and description aligned.
- `scripts/sync-local.sh` — update the `0.2.0` cache location.
- `benchmarks/test_activation_layer.py` — assert SessionStart reports pending decisions safely.

---

### Task 0: Close the existing delivery run and enter a clean feature task

**Files:**

- Read: `.ship/ship-auto.local.md`
- Read: `.ship/tasks/continue-yishuship-transformation-work-after-migrating-produ/control/run_state.yaml`
- Modify only through existing yishuship Review/QA/Handoff commands.

- [ ] **Step 1: Confirm the current gate**

Run:

```bash
cd /Users/mahaoxuan/Developer/yishuship
bash scripts/yishuship-bootstrap.sh status
```

Expected before implementation: `active_task: continue-yishuship-transformation-work-after-migrating-produ`, `phase: review`, `next_action: resume`.

- [ ] **Step 2: Finish the existing task without mixing feature edits into it**

Execute its current `/yishuship:review`, then `/yishuship:qa`, then `/yishuship:handoff` according to the existing run state. Fix only findings belonging to that task.

Re-run:

```bash
bash scripts/yishuship-bootstrap.sh status
```

Expected gate: the old task is no longer active. If Review or QA fails, stop here and loop on that failure.

- [ ] **Step 3: Enter a fresh decision-canvas task**

Run:

```bash
bash scripts/yishuship-bootstrap.sh enter "implement approved native decision canvas"
bash scripts/yishuship-bootstrap.sh status
```

Expected: a new task id, an active run state, and a State Sense for this feature.

---

### Task 1: Lock the event protocol with reducer tests

**Files:**

- Create: `package.json`
- Create: `decision-canvas/protocol.mjs`
- Create: `tests/decision-canvas/protocol.test.mjs`

- [ ] **Step 1: Add the dependency-free Node test surface**

Create `package.json`:

```json
{
  "name": "yishuship",
  "version": "0.2.0",
  "private": true,
  "type": "module",
  "scripts": {
    "test:canvas:unit": "node --test tests/decision-canvas/*.test.mjs",
    "test:canvas:e2e": "playwright test tests/decision-canvas/browser.spec.mjs",
    "test:canvas": "npm run test:canvas:unit && npm run test:canvas:e2e"
  }
}
```

- [ ] **Step 2: Write failing reducer tests for the full state chain**

Create `tests/decision-canvas/protocol.test.mjs` with tests that import these exact exports:

```js
import test from "node:test";
import assert from "node:assert/strict";
import {
  RevisionConflictError,
  applyCommand,
  initialDecisionState,
  reduceEvents,
} from "../../decision-canvas/protocol.mjs";

const actor = { kind: "user", id: "local-user" };
const clock = () => "2026-07-13T12:00:00.000Z";
const ids = (() => {
  let value = 0;
  return () => `event-${++value}`;
})();

test("proposal approval becomes one queued decision", () => {
  let state = initialDecisionState("facts-a");
  ({ state } = applyCommand(state, {
    type: "proposal.create",
    base_revision: state.revision,
    actor,
    payload: {
      title: "先完成会议纪要规则迁移",
      action: "完成 minutes route 的规则迁移并运行验收",
      rationale: "这是当前唯一进行中的交付切片",
      basis_refs: [".ship/tasks/current/control/run_state.yaml"],
      expected_impact: "关闭当前交付阻塞",
      alternatives: ["暂停当前切片并切换范围"],
      risks: ["旧规则兼容性回归"]
    }
  }, { now: clock, nextId: ids }));

  const proposalId = [...state.proposals.keys()][0];
  ({ state } = applyCommand(state, {
    type: "decision.approve",
    base_revision: state.revision,
    actor,
    proposal_id: proposalId,
    payload: {}
  }, { now: clock, nextId: ids }));

  assert.equal(state.queue.length, 1);
  assert.equal(state.queue[0].status, "queued");
  assert.equal(state.proposals.get(proposalId).status, "approved");
});

test("stale revision appends nothing", () => {
  const state = initialDecisionState("facts-a");
  assert.throws(
    () => applyCommand(state, {
      type: "proposal.create",
      base_revision: "facts-a:99",
      actor,
      payload: {
        title: "stale",
        action: "do not write",
        rationale: "stale base",
        basis_refs: [],
        expected_impact: "none",
        alternatives: [],
        risks: []
      }
    }, { now: clock, nextId: ids }),
    RevisionConflictError
  );
});
```

Add separate tests for:

- `proposal.revise` preserves history and changes current proposal content;
- `proposal.reject` never enters the queue;
- `decision.supersede` links old and new decisions without rewriting either;
- two claims against the same revision yield one `execution.claimed` event;
- `execution.interrupted` remains interrupted after replay and is not automatically queued;
- `execution.complete` without evidence becomes `needs_verification` and emits no `execution.completed`;
- `execution.complete` with an existing evidence ref becomes completed;
- `reduceEvents(events, factsRevision)` reproduces the same maps and queue.

- [ ] **Step 3: Run the tests and confirm the intended failure**

Run:

```bash
npm run test:canvas:unit
```

Expected: `ERR_MODULE_NOT_FOUND` for `decision-canvas/protocol.mjs`.

- [ ] **Step 4: Implement the pure protocol**

Create `decision-canvas/protocol.mjs` with these public contracts:

```js
export const EVENT_TYPES = new Set([
  "proposal.created",
  "proposal.revised",
  "proposal.rejected",
  "decision.approved",
  "decision.superseded",
  "execution.claimed",
  "execution.reported",
  "execution.interrupted",
  "execution.completed",
  "execution.failed",
]);

export class RevisionConflictError extends Error {
  constructor(expected, actual) {
    super(`base revision ${expected} does not match ${actual}`);
    this.code = "revision_conflict";
    this.expected = expected;
    this.actual = actual;
  }
}

export function initialDecisionState(factsRevision) {
  return {
    factsRevision,
    eventRevision: 0,
    revision: `${factsRevision}:0`,
    proposals: new Map(),
    decisions: new Map(),
    executions: new Map(),
    queue: [],
    events: [],
    corruption: null,
  };
}

export function applyCommand(state, command, runtime) {}
export function reduceEvents(events, factsRevision) {}
export function serializeState(state) {}
```

Implementation rules:

- Commands use dotted imperative names (`proposal.create`, `proposal.revise`, `proposal.reject`, `decision.approve`, `decision.supersede`, `decision.claim`, `execution.report`, `execution.interrupt`, `execution.complete`, `execution.fail`).
- Stored events use the approved past-tense names in `EVENT_TYPES`.
- Each event contains `event_id`, `event_revision`, `project_revision`, `base_revision`, `actor`, `type`, `proposal_or_decision_id`, `task_id`, `payload`, `evidence_refs`, `created_at`.
- `revision` is opaque and deterministic: `<facts sha256>:<event revision>`.
- Validate every required proposal field as a non-empty string or string array before creating an event.
- A claim succeeds only when the decision is queued and has no active claim.
- `execution.complete` first verifies every evidence path through the runtime callback `evidenceExists(ref)`; otherwise create `execution.reported` with status `needs_verification`.
- Never mutate the input state or prior event payloads.

- [ ] **Step 5: Make the reducer tests pass**

Run:

```bash
npm run test:canvas:unit
```

Expected: all protocol tests pass.

- [ ] **Step 6: Commit the protocol slice**

Run:

```bash
git add package.json decision-canvas/protocol.mjs tests/decision-canvas/protocol.test.mjs
git commit -m "feat(canvas): define durable decision protocol"
```

---

### Task 2: Persist events safely and recover deterministically

**Files:**

- Create: `decision-canvas/store.mjs`
- Create: `tests/decision-canvas/helpers.mjs`
- Create: `tests/decision-canvas/store.test.mjs`

- [ ] **Step 1: Write failing persistence tests**

Create helpers that initialize a temporary Git repo and return its canonical path. Then test these contracts:

```js
import {
  DecisionStore,
  ProjectLockedError,
} from "../../decision-canvas/store.mjs";

test("restart replays proposals decisions and queue", async () => {
  const project = await makeProject();
  const first = await DecisionStore.open(project, { cacheRoot: project.cache });
  const state = await first.getState("facts-a");
  await first.dispatch(createProposalCommand(state.revision), "facts-a");
  await first.close();

  const second = await DecisionStore.open(project.root, { cacheRoot: project.cache });
  const restored = await second.getState("facts-a");
  assert.equal(restored.proposals.size, 1);
  await second.close();
});
```

Add tests for:

- `events.jsonl` is created only on the first successful mutation;
- a second live `DecisionStore.open()` for the same project throws `ProjectLockedError`;
- a stale PID lock is reclaimed;
- concurrent dispatches serialize and only one claim succeeds;
- a truncated final JSONL line returns read-only state with `corruption.line` and rejects new writes;
- valid lines before corruption are preserved;
- closing releases the local project lease;
- event log permissions are no broader than `0644`, token/lease files no broader than `0600`.

- [ ] **Step 2: Run the persistence test and confirm failure**

Run:

```bash
node --test tests/decision-canvas/store.test.mjs
```

Expected: module-not-found for `decision-canvas/store.mjs`.

- [ ] **Step 3: Implement the store and project lease**

Create `decision-canvas/store.mjs` exporting:

```js
export class ProjectLockedError extends Error {}
export class CorruptEventLogError extends Error {}

export class DecisionStore {
  static async open(projectRoot, options = {}) {}
  async getState(factsRevision) {}
  async dispatch(command, factsRevision) {}
  async close() {}
}

export function projectIdentity(projectRoot) {}
export function replayJsonl(text, factsRevision) {}
```

Use these exact paths:

```text
<project>/.ship/decision-canvas/events.jsonl
<cacheRoot>/<repo-id>/decision-canvas-service.lock
```

Implementation rules:

- Canonicalize the root with `fs.realpath` and require it to contain `.git`.
- Derive `<repo-id>` as the first 20 hex characters of SHA-256(canonical root).
- Acquire the lease with `open(path, "wx", 0o600)` and store `{pid, projectRoot, startedAt}`.
- Treat the lease as stale only when its PID is absent; do not steal a live lease by age.
- Serialize mutations through one promise chain inside the store.
- Before append, replay the current file and compare `base_revision` again inside the serialized section.
- Append exactly one compact JSON object plus `\n`, call `FileHandle.sync()`, then close.
- On malformed JSON, record its 1-based line number, stop replay at the previous revision, set read-only mode, and reject all later writes.
- Never skip a malformed line and continue.

- [ ] **Step 4: Make persistence tests pass**

Run:

```bash
node --test tests/decision-canvas/protocol.test.mjs tests/decision-canvas/store.test.mjs
```

Expected: all tests pass, including restart, lock and corruption cases.

- [ ] **Step 5: Commit the persistence slice**

Run:

```bash
git add decision-canvas/store.mjs tests/decision-canvas/helpers.mjs tests/decision-canvas/store.test.mjs
git commit -m "feat(canvas): persist decisions as replayable events"
```

---

### Task 3: Project real Git and yishuship facts into a decision graph

**Files:**

- Create: `decision-canvas/projector.mjs`
- Create: `tests/decision-canvas/projector.test.mjs`

- [ ] **Step 1: Write a fixture that contains real project meaning**

In `tests/decision-canvas/projector.test.mjs`, use `makeProject()` to create:

```text
.ship/pm-state.yaml
.ship/tasks/meeting-minutes/control/run_state.yaml
.ship/tasks/meeting-minutes/product/01-strategy.md
.ship/tasks/meeting-minutes/product/08-prd.md
.ship/tasks/meeting-minutes/e2e/report.md
.ship/tasks/meeting-minutes/qa/report.md
.ship/tasks/meeting-minutes/delivery/handoff.md
package.json
```

Put concrete content in those files: goal “减少会议纪要整理时间”, capability “承诺提取与双向确认”, active work “会议纪要规则迁移”, risk “任务状态指针漂移”, and evidence “18/18 unit; 6/6 e2e”.

- [ ] **Step 2: Write failing graph assertions**

Assert the projector returns this shape:

```js
const projection = await projectProject(project.root);
assert.match(projection.factsRevision, /^[a-f0-9]{64}$/);
assert.ok(projection.nodes.some((node) =>
  node.kind === "goal" && node.title.includes("减少会议纪要整理时间")
));
assert.ok(projection.nodes.some((node) =>
  node.kind === "capability" && node.title.includes("承诺提取与双向确认")
));
assert.ok(projection.nodes.some((node) =>
  node.kind === "work" && node.title.includes("会议纪要规则迁移")
));
assert.ok(projection.nodes.some((node) =>
  node.kind === "risk" && node.title.includes("任务状态指针漂移")
));
assert.ok(projection.nodes.some((node) =>
  node.kind === "evidence" && node.summary.includes("18/18")
));
assert.equal(projection.nodes.some((node) => node.title === "review"), false);
```

Also assert:

- each factual node has at least one `source_ref` with a project-relative path;
- nodes include `source_revision` and `epistemic_status: "fact"`;
- edges connect goal → capability → active work → evidence/risk where sources establish that relation;
- Git branch, HEAD and dirty paths appear as graph metadata, not as fake product nodes;
- conflicting active-task pointers create a `risk` node instead of silently choosing one;
- a deleted source changes the old node to `source_missing` on the next projection;
- package `test*` scripts appear under `declaredChecks` but are not automatically executed.

- [ ] **Step 3: Confirm the test fails**

Run:

```bash
node --test tests/decision-canvas/projector.test.mjs
```

Expected: module-not-found for `decision-canvas/projector.mjs`.

- [ ] **Step 4: Implement the projector**

Create `decision-canvas/projector.mjs` with:

```js
export async function projectProject(projectRoot) {}
export function extractMarkdownSections(markdown) {}
export function extractYamlScalars(text) {}
export function buildFactGraph(snapshot) {}
```

Projection order:

1. Canonical root, Git branch, HEAD and porcelain status.
2. `.ship/pm-state.yaml` and every `.ship/tasks/*/control/run_state.yaml`.
3. For the active task, read known product, plan, Review, QA, E2E and Handoff artifacts only.
4. Parse Markdown headings and bullets using a small deterministic section extractor. Recognize bilingual heading families for goal/outcome, capability/scope, active work, risk/known limit/blocker, evidence/test/acceptance, and open question.
5. Read `package.json` scripts whose key contains `test`, `check`, `lint`, `typecheck`, or `build` into `declaredChecks`.
6. Hash sorted `{git, source path, source content hash}` records into `factsRevision`.

Graph node contract:

```js
{
  id: "fact:<sha256-prefix>",
  kind: "goal|capability|work|evidence|risk|question",
  title: "human project content",
  summary: "one concise source-backed explanation",
  status: "verified|active|risk|open|source_missing",
  epistemic_status: "fact",
  source_refs: [{ path, heading, line }],
  source_revision: "<git head or worktree>"
}
```

Never create `design`, `dev`, `review`, `qa`, or `handoff` as main nodes. Those values may appear only in `phase` metadata.

- [ ] **Step 5: Make projection tests pass**

Run:

```bash
node --test tests/decision-canvas/projector.test.mjs
```

Expected: all real-object, source, conflict and missing-source assertions pass.

- [ ] **Step 6: Commit the projection slice**

Run:

```bash
git add decision-canvas/projector.mjs tests/decision-canvas/projector.test.mjs
git commit -m "feat(canvas): project repository truth into graph"
```

---

### Task 4: Expose one authenticated HTTP/SSE decision service

**Files:**

- Create: `decision-canvas/service.mjs`
- Create: `scripts/decision-canvas.mjs`
- Create: `tests/decision-canvas/service.test.mjs`

- [ ] **Step 1: Write failing service tests**

Use an in-process server on port `0`. Test these exact routes:

| Method | Route | Authority |
|---|---|---|
| `GET` | `/api/state` | browser/Agent read |
| `GET` | `/api/events` | browser SSE read |
| `POST` | `/api/proposals` | user or Agent create |
| `POST` | `/api/proposals/:id/revise` | browser user only |
| `POST` | `/api/proposals/:id/reject` | browser user only |
| `POST` | `/api/proposals/:id/approve` | browser user only |
| `POST` | `/api/decisions/:id/supersede` | browser user only |
| `POST` | `/api/decisions/claim-next` | Agent only |
| `POST` | `/api/executions/:id/report` | Agent only |

Tests must prove:

- missing/wrong bearer token returns `401`;
- the service cannot switch to another project root;
- successful mutation returns `{state, appendedEvent}` and publishes one SSE `state.changed` event;
- stale approval returns `409` with `{code:"revision_conflict", current_revision, changed_since}`;
- two concurrent claim requests produce one `200` claim and one `204` no-content result;
- completion without evidence returns `422 evidence_required` and leaves execution `needs_verification`;
- service close releases the project lease;
- static file traversal such as `/../store.mjs` returns `404`.

- [ ] **Step 2: Confirm service tests fail**

Run:

```bash
node --test tests/decision-canvas/service.test.mjs
```

Expected: module-not-found for `decision-canvas/service.mjs`.

- [ ] **Step 3: Implement the HTTP/SSE service**

Create `decision-canvas/service.mjs` exporting:

```js
export async function createDecisionCanvasService({
  projectRoot,
  host = "127.0.0.1",
  port = 0,
  token,
  cacheRoot,
}) {}
```

Return `{url, token, close, refresh, address}`. Service rules:

- Reject a non-loopback `host` before listening.
- Accept `Authorization: Bearer <token>` on every `/api/*` route.
- Limit JSON bodies to 256 KiB.
- Set `Cache-Control: no-store`, `X-Content-Type-Options: nosniff`, and a restrictive CSP for HTML.
- Hold one `DecisionStore` for the lifetime of the service; it is the only writer.
- Re-project facts before every mutation, so stale Git/`.ship` facts invalidate `base_revision`.
- Publish SSE frames as `event: state.changed\ndata: <json>\n\n`.
- Heartbeat idle SSE clients every 15 seconds and remove closed sockets.
- Serve only files below `decision-canvas/web/`.
- Pass an explicit `actor_channel` (`browser` or `agent`) to route authorization; reject approval/revision/rejection from `agent`.

- [ ] **Step 4: Implement the CLI and local service descriptor**

Create `scripts/decision-canvas.mjs` with:

```text
node scripts/decision-canvas.mjs start   --project /absolute/project
node scripts/decision-canvas.mjs serve   --project /absolute/project
node scripts/decision-canvas.mjs status  --project /absolute/project --json
node scripts/decision-canvas.mjs stop    --project /absolute/project
node scripts/decision-canvas.mjs open    --project /absolute/project
node scripts/decision-canvas.mjs pending --project /absolute/project --json
```

Use this local descriptor:

```text
~/.cache/yishuship/<repo-id>/decision-canvas-service.json
```

Descriptor shape:

```json
{
  "projectRoot": "/canonical/project",
  "pid": 12345,
  "port": 49152,
  "token": "64-hex-characters",
  "startedAt": "2026-07-13T12:00:00.000Z"
}
```

Rules:

- Generate the token with `randomBytes(32).toString("hex")` and write descriptor mode `0600`.
- `start` is idempotent: return an existing healthy descriptor or spawn detached `serve` and wait up to five seconds for `/api/state`.
- `open` calls `start`, then opens `http://127.0.0.1:<port>/#token=<token>` using macOS `open`; on non-macOS print the URL.
- `pending` reads/replays the event log without starting a service and returns queued/claimed counts.
- `stop` sends `SIGTERM`, waits for exit, and removes only the matching descriptor.

- [ ] **Step 5: Make service tests pass**

Run:

```bash
node --test tests/decision-canvas/service.test.mjs
```

Expected: auth, SSE, stale revision, single claim and evidence gate all pass.

- [ ] **Step 6: Smoke the real CLI lifecycle**

Run:

```bash
node scripts/decision-canvas.mjs start --project /Users/mahaoxuan/Developer/yishuship
node scripts/decision-canvas.mjs status --project /Users/mahaoxuan/Developer/yishuship --json
node scripts/decision-canvas.mjs stop --project /Users/mahaoxuan/Developer/yishuship
```

Expected: healthy → stopped; no server remains bound afterward.

- [ ] **Step 7: Commit the service slice**

Run:

```bash
git add decision-canvas/service.mjs scripts/decision-canvas.mjs tests/decision-canvas/service.test.mjs
git commit -m "feat(canvas): add local decision service"
```

---

### Task 5: Build the real spatial decision interface

**Files:**

- Create: `decision-canvas/web/index.html`
- Create: `decision-canvas/web/app.js`
- Create: `decision-canvas/web/styles.css`
- Create: `playwright.config.mjs`
- Create: `tests/decision-canvas/browser.spec.mjs`
- Create: `package-lock.json`
- Modify: `package.json`
- Modify: `.gitignore`

- [ ] **Step 1: Install the development-only browser test dependency**

Run:

```bash
npm install --save-dev @playwright/test
npx playwright install chromium
```

Expected: `package-lock.json` is created; runtime dependencies remain empty.

Append to `.gitignore`:

```text
node_modules/
playwright-report/
test-results/
```

- [ ] **Step 2: Write the failing browser decision-loop test**

Create `playwright.config.mjs` with one Chromium project, headless mode, one worker, and no retries locally.

Create `tests/decision-canvas/browser.spec.mjs` that:

1. starts a real service against a temporary Git/`.ship` project;
2. opens `/#token=<token>`;
3. asserts goal/capability/work/evidence/risk nodes are visible in a spatial canvas;
4. selects a fact and verifies “解释依据” and “查看来源” change the inspector content;
5. creates a user proposal through the form;
6. edits it, approves it, and sees `queued` without reload;
7. calls the Agent claim endpoint and sees `claimed` through SSE;
8. reports completion first without evidence and sees `needs verification`;
9. creates an evidence file, reports again, and sees `completed`;
10. drags one node, reloads, and sees its position restored from `localStorage`.

The test must click by accessible role/name, not CSS implementation details.

- [ ] **Step 3: Confirm the E2E test fails**

Run:

```bash
npm run test:canvas:e2e
```

Expected: `/` returns 404 or required accessible canvas elements are missing.

- [ ] **Step 4: Implement accessible shell and inspector markup**

Create `decision-canvas/web/index.html` with:

- header: project name, revision, connection state, fit-view control;
- `<main aria-label="项目决策画布">` containing a pan/zoom viewport;
- SVG edge layer below positioned node buttons;
- right `<aside aria-label="节点检查器">`;
- proposal dialog/form with fields matching protocol requirements;
- connection-loss banner that makes all mutations disabled but leaves reading available.

No inline script, no remote fonts, no CDN assets.

- [ ] **Step 5: Implement native spatial interaction and real commands**

Create `decision-canvas/web/app.js` around one plain state object:

```js
const model = {
  project: null,
  revision: null,
  nodes: new Map(),
  edges: [],
  selectedId: null,
  view: { x: 0, y: 0, zoom: 1, positions: {} },
  connected: false,
};
```

Required behavior:

- Parse the token from `location.hash`, then immediately remove it from the visible URL with `history.replaceState`.
- Fetch `/api/state` with bearer auth.
- Consume `/api/events` using streaming `fetch` so auth stays in the header; reconcile by replacing server state, never by guessing local mutations.
- Lay out missing positions by semantic lanes: goal left; capability/work center; evidence/risk right; proposals/decisions/executions below the objects they affect.
- Render real nodes as keyboard-focusable buttons and edges in SVG.
- Support background pan, wheel zoom, node drag, fit view, and keyboard selection.
- Persist only `{x,y,zoom,positions,inspectorOpen}` under `localStorage["yishuship.canvas.<repo-id>"]`.
- “解释依据” renders source-backed meaning and epistemic status.
- “查看来源” renders every project-relative path/heading/line and offers a copy-path action.
- Proposal controls call the real revise/reject/approve endpoints with current `base_revision`.
- On `409`, reload state and show the changed-since summary before re-enabling approval.
- When SSE disconnects, enter read-only mode. Reconnect with bounded exponential backoff.

- [ ] **Step 6: Implement the visual system**

Create `decision-canvas/web/styles.css` with:

- a dotted infinite-canvas background;
- restrained neutral surface colors;
- green verified, blue active, amber risk, purple proposal/scope;
- distinct selected and keyboard-focus rings;
- 220–280px node widths, compact source/status metadata, readable inspector;
- reduced-motion support;
- minimum 44px interactive targets;
- responsive fallback where the inspector overlays rather than shrinking the canvas below usability.

Do not recreate the earlier horizontal text-flow list. The viewport must visibly support two-dimensional placement and direct manipulation.

- [ ] **Step 7: Make the browser loop pass**

Run:

```bash
npm run test:canvas:e2e
```

Expected: the complete proposal → approval → claim → evidence completion loop passes in Chromium.

- [ ] **Step 8: Commit the browser slice**

Run:

```bash
git add package.json package-lock.json playwright.config.mjs .gitignore decision-canvas/web tests/decision-canvas/browser.spec.mjs
git commit -m "feat(canvas): add spatial decision interface"
```

---

### Task 6: Give Codex and Claude Code the same four MCP tools

**Files:**

- Create: `.mcp.json`
- Create: `decision-canvas/mcp.mjs`
- Create: `tests/decision-canvas/mcp.test.mjs`

- [ ] **Step 1: Write a failing MCP contract probe**

Create `tests/decision-canvas/mcp.test.mjs` that spawns `node decision-canvas/mcp.mjs`, sends newline-delimited JSON-RPC, and asserts:

- `initialize` returns server name `yishuship-decision-canvas` and protocol version `2024-11-05`;
- `tools/list` returns exactly `get_project_state`, `submit_proposal`, `claim_next_decision`, `report_execution`;
- no tool name contains `approve`, `reject`, `revise`, or `supersede`;
- every tool requires `project_root`;
- `submit_proposal` creates an Agent-authored proposal through the HTTP service;
- `claim_next_decision` returns the same decision id/revision visible in browser state;
- two spawned MCP processes cannot both claim the same decision;
- `report_execution` enforces the same evidence rule as HTTP;
- after the first valid `project_root`, the MCP process rejects a different root.

- [ ] **Step 2: Confirm the contract probe fails**

Run:

```bash
node --test tests/decision-canvas/mcp.test.mjs
```

Expected: module-not-found for `decision-canvas/mcp.mjs`.

- [ ] **Step 3: Implement the minimal stdio MCP adapter**

Create `decision-canvas/mcp.mjs` with handlers for:

```text
initialize
notifications/initialized
ping
tools/list
tools/call
```

Tool input contracts:

```js
get_project_state({ project_root })

submit_proposal({
  project_root,
  base_revision,
  title,
  action,
  rationale,
  basis_refs,
  expected_impact,
  alternatives,
  risks
})

claim_next_decision({
  project_root,
  base_revision,
  agent_id,
  task_id
})

report_execution({
  project_root,
  base_revision,
  execution_id,
  status: "reported|interrupted|completed|failed",
  summary,
  evidence_refs
})
```

Adapter rules:

- On the first tool call, canonicalize and pin `project_root`; reject root changes for that MCP process.
- Use `scripts/decision-canvas.mjs start` semantics to ensure one service exists, then call it over authenticated HTTP. Do not open a second store.
- Return MCP text content containing compact JSON and set `isError: true` for protocol/business errors.
- Map `409` to `revision_conflict`, `422` to `evidence_required`, and empty queue to `{claimed:false}`.
- Ignore notifications without writing to stdout; logs go to stderr only.
- Keep approval/revision/rejection/supersession absent from both tool list and dispatch table.

- [ ] **Step 4: Register the adapter for both plugin hosts**

Create `.mcp.json`:

```json
{
  "mcpServers": {
    "yishuship-decision-canvas": {
      "command": "node",
      "args": ["./decision-canvas/mcp.mjs"],
      "cwd": ".",
      "tool_timeout_sec": 60
    }
  }
}
```

- [ ] **Step 5: Make the MCP contract pass**

Run:

```bash
node --test tests/decision-canvas/mcp.test.mjs
```

Expected: both host-neutral protocol behavior and single-claim semantics pass.

- [ ] **Step 6: Verify host registration locally**

Run:

```bash
codex mcp list
claude mcp list
```

Expected after local plugin sync: `yishuship-decision-canvas` is registered in both hosts. If either host does not consume plugin `.mcp.json`, document that host's one-time local registration command in the operations guide; do not create a second protocol implementation.

- [ ] **Step 7: Commit the adapter slice**

Run:

```bash
git add .mcp.json decision-canvas/mcp.mjs tests/decision-canvas/mcp.test.mjs
git commit -m "feat(canvas): share decisions across agent hosts"
```

---

### Task 7: Integrate the canvas into yishuship routing and safe boundaries

**Files:**

- Create: `scripts/decision-boundary.sh`
- Create: `skills/canvas/SKILL.md`
- Modify: `scripts/session-start.sh`
- Modify: `scripts/auto-orchestrate.sh`
- Modify: `hooks/hooks.json`
- Modify: `hooks/codex-hooks.json`
- Modify: `skills/use-yishuship/SKILL.md`
- Modify: `skills/.shared/runtime-resolution.md`
- Modify: `benchmarks/test_activation_layer.py`

- [ ] **Step 1: Add failing activation-contract tests**

Extend `benchmarks/test_activation_layer.py` to create an approved queued decision in a temporary repo and assert:

- `scripts/session-start.sh` includes `<YISHUSHIP_DECISIONS>` with count and decision id;
- without an event log, the section is absent and startup remains fast;
- the hook never starts the local HTTP service;
- malformed event logs report `decision_canvas: corrupt` without crashing SessionStart;
- `scripts/decision-boundary.sh` is non-blocking and exits `0` even when no service is running.

Add a source-contract assertion that `auto-orchestrate.sh` emits `PENDING_DECISIONS` from `emit_dispatch` and `emit_dispatch_parallel_verify`, which are the safe phase boundaries.

- [ ] **Step 2: Confirm the new activation tests fail**

Run:

```bash
python3 benchmarks/test_activation_layer.py -v
```

Expected: missing decision section/boundary integration assertions fail.

- [ ] **Step 3: Implement the non-blocking boundary reader**

Create `scripts/decision-boundary.sh`:

- drain hook stdin;
- resolve the project root from Git or `pwd`;
- if `.ship/decision-canvas/events.jsonl` is absent, exit `0` without starting Node service;
- run `node scripts/decision-canvas.mjs pending --project "$ROOT" --json`;
- print one concise message only when queued or claimed decisions exist, or when the log is corrupt;
- never claim a decision and never block Stop.

- [ ] **Step 4: Wire safe boundaries**

Modify `scripts/session-start.sh` to append:

```text
<YISHUSHIP_DECISIONS>
queued: <number>
claimed: <number>
next_decision_id: <id or none>
Consume only after the current atomic action; do not treat this hint as approval to interrupt work.
</YISHUSHIP_DECISIONS>
```

only when the log exists.

Modify `auto-orchestrate.sh` so dispatch functions emit:

```text
PENDING_DECISIONS:<number>
```

after the existing action fields. This is informational; it does not change the current phase or dispatch.

Add `scripts/decision-boundary.sh` after existing Stop gates in `hooks/hooks.json` and `hooks/codex-hooks.json`.

- [ ] **Step 5: Add the `/yishuship:canvas` skill**

Create `skills/canvas/SKILL.md` with frontmatter name `canvas`, description covering “画布 / 项目地图 / 决定下一步 / proposal / decision canvas”, and only the tools required to run the CLI and inspect status.

Skill behavior:

1. run bootstrap status and respect any active task;
2. run `node scripts/decision-canvas.mjs open --project "$(git rev-parse --show-toplevel)"`;
3. report the local URL and current queued/claimed counts;
4. explain that user approval happens in the browser and Agents consume only approved decisions;
5. never auto-approve or auto-claim merely because the canvas was opened.

Update `skills/use-yishuship/SKILL.md` so requests to open/show/use the project decision canvas route directly to `/yishuship:canvas`.

Update `skills/.shared/runtime-resolution.md` with one shared protocol table and the four MCP tools; keep the existing peer-dispatch rules unchanged.

- [ ] **Step 6: Make activation tests pass**

Run:

```bash
python3 benchmarks/test_activation_layer.py -v
node --test tests/decision-canvas/protocol.test.mjs tests/decision-canvas/store.test.mjs tests/decision-canvas/projector.test.mjs tests/decision-canvas/service.test.mjs tests/decision-canvas/mcp.test.mjs
```

Expected: SessionStart, phase-boundary and all decision protocol tests pass.

- [ ] **Step 7: Commit the host-integration slice**

Run:

```bash
git add scripts/decision-boundary.sh scripts/session-start.sh scripts/auto-orchestrate.sh hooks/hooks.json hooks/codex-hooks.json skills/canvas/SKILL.md skills/use-yishuship/SKILL.md skills/.shared/runtime-resolution.md benchmarks/test_activation_layer.py
git commit -m "feat(canvas): integrate decision boundaries"
```

---

### Task 8: Package, document, and validate the real-project release

**Files:**

- Create: `docs/operations/yishuship-decision-canvas.md`
- Modify: `AGENTS.md`
- Modify: `README.md`
- Modify: `.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `scripts/sync-local.sh`
- Modify: `DEVLOG.md`

- [ ] **Step 1: Update plugin metadata and skill count**

Set both plugin manifests to version `0.2.0`. Add `decision-canvas`, `project-map`, and `human-agent-collaboration` keywords/descriptions without removing the lifecycle positioning.

Update `scripts/sync-local.sh` default Codex/Claude cache paths from `0.1.0` to `0.2.0`.

Update `AGENTS.md`:

- add `canvas/` to the repository map;
- change the expected skill count from `14` to `15`;
- add `npm run test:canvas:unit` and `npm run test:canvas:e2e` as validation commands.

- [ ] **Step 2: Write the operator guide**

Create `docs/operations/yishuship-decision-canvas.md` covering exact commands for:

- open, status and stop;
- how proposal approval differs from Agent claiming;
- where semantic events and local view/service state live;
- stale-revision recovery;
- corrupt-log read-only recovery without deleting history;
- interrupted execution handling;
- Codex/Claude MCP verification;
- local-only security boundary;
- uninstall/disable behavior that leaves `.ship/decision-canvas/events.jsonl` readable as plain JSONL.

- [ ] **Step 3: Update README and development history**

Add one concise README section showing:

```text
Git + tests + .ship facts
          ↓
   decision canvas
    ↙           ↘
user approval   Agent proposal/result
          ↓
 durable execution queue
```

Document `/yishuship:canvas`, the four MCP tools, and the runtime/no-Canvasight boundary. Add a dated `DEVLOG.md` entry linking the approved spec, implementation plan, tests and operations guide.

- [ ] **Step 4: Run the full repository acceptance surface**

Run:

```bash
python3 -m unittest discover -s benchmarks -p 'test_*.py' -v
npm run test:canvas
bash scripts/sync-local.sh --check
find skills -name SKILL.md | wc -l
rg -n "Canvasight|@xyflow/react|react|zustand" decision-canvas package.json
```

Expected:

- all Python and Node/Playwright tests pass;
- skill count is `15`;
- runtime source contains no Canvasight/React/XYFlow/Zustand dependency;
- sync check may report caches behind before apply, but no broken skill link logic.

- [ ] **Step 5: Verify the accepted real project**

Use `/Users/mahaoxuan/Desktop/黑客松/fc-opc-ibot`:

```bash
node scripts/decision-canvas.mjs open --project /Users/mahaoxuan/Desktop/黑客松/fc-opc-ibot
```

Manual QA must confirm:

1. main nodes contain FC-OPC goals, delivered capability, current meeting-minutes work, test evidence and actual risks—not yishuship phases;
2. “解释依据” changes the inspector and “查看来源” shows real source references;
3. Agent proposal appears live;
4. user edit + approval becomes one queued decision;
5. Codex and Claude return the same decision id and revision;
6. one of two claim attempts wins;
7. restart preserves state;
8. interrupted execution does not re-run;
9. completion is blocked until evidence exists;
10. node positions persist locally and do not dirty the project Git worktree.

Record results in the active task's QA/E2E artifacts, including commands, screenshots, failures and evidence paths.

- [ ] **Step 6: Sync installed surfaces and re-check both hosts**

Run only after all acceptance checks pass:

```bash
bash scripts/sync-local.sh --apply
bash scripts/sync-local.sh --check
codex mcp list
claude mcp list
```

Expected: skill links `15/15`, plugin caches at the release commit, MCP server visible in both hosts.

- [ ] **Step 7: Final release commit**

Run:

```bash
git add AGENTS.md README.md DEVLOG.md docs/operations/yishuship-decision-canvas.md .claude-plugin/plugin.json .claude-plugin/marketplace.json scripts/sync-local.sh package.json package-lock.json
git commit -m "docs(canvas): ship native decision workflow"
git status --short
```

Expected: only the pre-existing untracked `.superpowers/` prototype directory remains; no decision-canvas implementation file is uncommitted.

---

## Final Verification Matrix

| Approved requirement | Automated proof | Manual proof |
|---|---|---|
| Real project objects, not phase nodes | `projector.test.mjs` | FC-OPC QA item 1 |
| Agent proposal appears live | `service.test.mjs`, `browser.spec.mjs` | FC-OPC item 3 |
| User-only revise/reject/approve | `service.test.mjs`, `mcp.test.mjs` | inspector controls |
| Same decision across Codex/Claude | `mcp.test.mjs` | FC-OPC item 5 |
| No mid-action interruption | activation boundary tests | observe current atomic action |
| Single claim under concurrency | protocol/store/service/MCP tests | FC-OPC item 6 |
| Stale revision rejected | protocol/service/browser tests | changed-since dialog |
| Restart recovery | `store.test.mjs` | FC-OPC item 7 |
| Interrupted work does not auto-run | protocol/browser tests | FC-OPC item 8 |
| Evidence required for completion | protocol/service/browser tests | FC-OPC item 9 |
| No Canvasight runtime dependency | dependency scan | plugin install/open |

## Execution Stop Conditions

Stop and return to the user instead of improvising if any of these occurs:

- the old active yishuship task cannot pass Review/QA;
- either host cannot load plugin MCP configuration and needs a user-scoped external configuration change;
- the approved event schema must change in a way that alters user/Agent authority;
- browser E2E requires a runtime dependency rather than a development-only dependency;
- real project projection cannot identify source-backed goals/capabilities without a new product decision.
