# yishuship index

yishuship holds only the management: remember each idea, stop to ask, show
evidence. How any particular kind of work is done lives elsewhere. This is the
map to it.

Open an entry only when its moment comes. Most slices need one or two entries,
some need none; a small, obvious change does not earn a whole method.

Three levels, same format, all read:

- this file: general, true for anyone and any project;
- `~/.yishuship/INDEX.md`: the user's own, by kind of work, across projects;
- `<project>/.ship/INDEX.md`: facts about one project only.

yishuship itself never names a specific project. In the done report, say which
entries this slice used and what the index lacked, and at which level.

`<yishuship>` below means the plugin root, two levels above any skill folder.

| When | Open |
|---|---|
| Judging whether an idea is worth building, or choosing between approaches | `skill:think` |
| Something errors, crashes, regresses, or used to work | `skill:hunt` |
| Someone points at a URL or PDF | `skill:read` |
| Before a release, publish, deploy, or merge to main | `skill:check` |
| Verifying visible behavior in a running macOS app | `docs/real-app.md` |
| Showing structure: behaviors that cross screens or branch, or the shape of a change before building | `docs/diagrams.md` |

## Keeping it true

Every path and skill named in a table row must exist. Check with
`python3 <yishuship>/scripts/check-index.py`; `/yishuship:ideas` runs it too.
When a resource moves, fix the row, not the reader.
