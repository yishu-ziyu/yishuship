## Engineering Goal

Keep local Claude Code yishuship usage synchronized with `https://github.com/yishu-ziyu/ship.git` and expose reliable `/yishuship:*` skills.

## Product Context

The user uses yishuship as the shared collaboration process between themselves and AI agents.

Recent confusion came from stale plugin state and old Ship references.

## Requirements

- `scripts/sync-local.sh` provides check and apply modes.
- SessionStart points to `/yishuship:use-yishuship`.
- Plugin metadata points to `https://github.com/yishu-ziyu/ship`.
- `/yishuship:*` links expose all 13 skills.
- Local sync never pulls over dirty work.

## Acceptance Criteria

- `/Users/mahaoxuan/Developer/yishuship/scripts/sync-local.sh --check-remote` reports `skill_links: 13/13`.
- SessionStart output contains `/yishuship:use-yishuship`.
- Installed plugin cache metadata contains `https://github.com/yishu-ziyu/ship`.
- `claude plugin list --json` shows `yishuship@yishuship` enabled.

## Constraints

Do not remove unrelated marketplaces or plugins.

Do not create background watchers without explicit user approval.

Do not commit or push automatically.

## Source Artifacts

- `product/00-product-type.yaml`
- `product/01-strategy.md`
- `product/02-research.md`
- `product/03-problem-solution.md`
- `product/04-product-blueprint.md`
- `product/08-prd.md`
- `product/09-tech-project-plan.md`
- `docs/operations/yishuship-sync.md`
