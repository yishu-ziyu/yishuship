---
type: command
---
git diff --quiet base && test -z "$(git status --porcelain)"
