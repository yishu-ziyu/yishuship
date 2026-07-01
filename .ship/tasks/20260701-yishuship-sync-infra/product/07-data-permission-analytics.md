# Reports, Tracking, Permissions

## Report Design

The sync status report is intentionally short:

- `repo_head`
- `remote_main`
- `installed_plugin`
- `installed_path`
- `manifest_repository`
- `skill_links`
- `working_tree`
- `update_needed`

## Tracking Plan

No analytics pipeline is required.

Use git history for code changes, `.ship/tasks/<task_id>/` for workflow artifacts, and durable memory for cross-session facts.

## Permission Model

Allowed without confirmation:

- Read local yishuship status.
- Create or repair `/yishuship:*` symlinks that point to the yishuship repo.
- Reinstall the enabled yishuship plugin from the configured local marketplace.

Requires confirmation:

- Deleting marketplaces or unrelated plugins.
- Removing non-symlink files.
- Pulling over a dirty working tree.
- Creating LaunchAgents or background watchers.
- Pushing commits.

## Risk Controls

`--apply` skips `git pull` when the yishuship repo has uncommitted changes.

The script does not remove heliohq/ship marketplace entries.

The script does not commit, push, or delete project `.ship` state.
