# Entry choice + 玄米 flow mapping

> Companion to [yishuship-usage.md](yishuship-usage.md).  
> Goal: stop using the wrong entry, and map company delivery language to skills.

## Auto is not a smart router

`/yishuship:auto` is a **fixed spine** (state machine in
`scripts/auto-orchestrate.sh`):

```text
pm_intake
  → [Human Go await]   # DEC-0009, default on
  → design
  → dev
  → e2e ∥ review
  → qa
  → refactor
  → handoff
```

It does **not** pick stages from a product process table. Flexibility comes from:

| Entry | When |
|-------|------|
| `/yishuship:use-yishuship` | Phase unclear; want lightest path |
| Single skill (`pm-intake`, `design`, `dev`, …) | You know the stage |
| `/yishuship:auto` | Explicit end-to-end, idea → PR |

## OPC / super-individual default

| Situation | Call |
|-----------|------|
| New idea / 做不做不清 | `pm-intake` → **you Go** (`00c`) → then `design` / `dev` |
| Plan already exists | `design` or `dev` |
| Only verify | `qa` / `e2e` |
| Only ship | `handoff` |
| Full conveyor (accept waiting for Go) | `auto` |

Do **not** open auto for “chat a bit / one small cut” — it will feel rigid.

## Human Go (立项对应)

| Artifact | Meaning |
|----------|---------|
| `product/00c-go-decision.md` | Decision + budget + acceptance + human approval |
| `status: pending` | Materials ready; not committed |
| `status: approved` | You立项 / Go |
| No-Go | Stop; no design under auto |

Approve:

```bash
bash scripts/auto-orchestrate.sh approve_go
# or edit 00c Human approval → status: approved, then:
bash scripts/auto-orchestrate.sh resume
```

Disable only for CI: `require_human_go: false` or `YISHUSHIP_REQUIRE_HUMAN_GO=0`.

## 玄米流程 → yishuship

| 玄米 | Meaning | yishuship |
|------|---------|-----------|
| 需求来源 | Who hurts | `pm-intake` idea + research |
| 评估 | Worth / feasible | scope challenge + strategy Do/Don't |
| 立项 | Org commits | **Human Go** on `00c` |
| 排期 | Rough when | `09-tech-project-plan` milestones |
| 负责人 + 对接圈 | Who you serve | roles + design-spec constraints |
| 设计讨论 | Coarse design + research | `design` (+ `arch-design` if needed) |
| 组件/服务骨架 | Enable others | design constraints + first `dev` slice |
| 开发 | Build | `dev` |
| 测试环境部署 | Not only localhost | qa/e2e **precondition** (no separate skill) |
| 联调 | Run with counterparts | `qa` + `e2e` |
| 评审 | Stakeholder accept | peer-review + `review` + demo |
| 正式提测 | Formal test pass | `qa` again + durable `e2e` |
| 性能 | Load off-prod | qa checklist extension |
| 上线 | Production | `handoff` |
| 维护 | Next loop | new task or growth after handoff |

## Deploy / 联调 note

There is no `/yishuship:deploy` phase. Before `qa`/`e2e`, the environment must
be startable and reachable; put acceptance lines in PRD / design-spec.

## Related

- [DEC-0009 Human Go](../decisions/DEC-0009-human-go-gate.md)
- [activation.md](activation.md)
