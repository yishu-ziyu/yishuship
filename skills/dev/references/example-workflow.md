# Dev Example Workflow

Condensed example of the implement → review → fix loop.

```text
[Dev] Starting — 5 stories, test cmd: npm test
[Dev] Pattern references:
  Story 1 "User model" -> models/account.ts, tests/models/account.test.ts
  Story 2 "Product model" -> models/catalog-item.ts
[Dev] Dependency analysis:
  Wave 1: [Story 1 "User model", Story 2 "Product model"] <- parallel
  Wave 2: [Story 3 "User API", Story 4 "Product API"]     <- parallel
  Wave 3: [Story 5 "Auth middleware"]                      <- single-story

=== Wave 1 (parallel, 2 stories, same branch) ===

[Dev] WAVE_BASE_SHA = abc1234. Dispatching 2 Agent subagents in parallel.
      Story 1 subagent: DONE — edited models/user.ts, committed abc5
      Story 2 subagent: DONE — edited models/product.ts, committed abc6
[Dev] Peer reviews each story's commits — both PASS.

=== Wave 2 (parallel, 2 stories) ===

[Dev] Subagents implement stories 3, 4 in parallel on same branch.
      Story 3 subagent: DONE — routes/users.ts
      Story 4 subagent: DONE — routes/products.ts
[Dev] Peer reviewer -> Story 3 FAIL: missing input validation.
[Dev] Dispatching a fresh subagent to fix Story 3.
      Fix subagent: DONE — commit abc9, TEST_CMD PASS.
[Dev] Re-dispatch peer reviewer for Story 3 -> PASS (round 2/2).
[Dev] Story 4 -> PASS.

=== Wave 3 (single story) ===

[Dev] I implement Story 5 directly. Commit, TEST_CMD -> PASS.
[Dev] Peer reviewer -> PASS_WITH_CONCERNS ("jwt secret hardcoded in test fixtures").
[Dev] Append the concern to concerns.md.

=== Phase 3: Cross-Story Regression ===

[Dev] Run full test suite: npm test -> PASS (47 tests).
[Dev] DONE_WITH_CONCERNS — 5/5 stories, 3 waves, 1 concern recorded.
```
