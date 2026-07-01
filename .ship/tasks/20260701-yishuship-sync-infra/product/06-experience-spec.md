# Experience Spec

## Key Screens

There is no visual UI.

The main user-facing surface is terminal output from `scripts/sync-local.sh` and the small SessionStart hint injected by yishuship.

## Core States

Healthy state:

```text
repo_head: <sha>
remote_main: <same sha>
installed_plugin: <same sha>
skill_links: 13/13
update_needed: no
```

Remote ahead:

```text
update_needed: repo differs from origin/main
```

Plugin cache stale:

```text
update_needed: installed plugin differs from local repo
```

Skill exposure broken:

```text
skill_links: 12/13
missing_or_wrong_links: yishuship:pm-intake
```

Dirty repository:

```text
working_tree: dirty
```

In dirty state, `--apply` must skip `git pull`.

## Empty, Loading, Error States

If the repository path is missing, the script fails loudly.

If `claude` is missing, the script repairs skill links but reports that plugin refresh was skipped.

If a skill target path is a real non-symlink file, the script must not overwrite it.

## Golden Journeys

Fresh session check:

```bash
/Users/mahaoxuan/Developer/yishuship/scripts/sync-local.sh --check-remote
```

Safe refresh:

```bash
/Users/mahaoxuan/Developer/yishuship/scripts/sync-local.sh --apply
```

Then use:

```text
/yishuship:use-yishuship
```
