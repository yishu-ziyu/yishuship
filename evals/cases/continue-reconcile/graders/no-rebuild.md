---
type: command
---
# Fixing a bug in the shipped slice is fine; rewriting the tag filter itself is not.
! git diff base -- todo.py | grep -E '^[-+].*(def list_items|item.get\("tag"\) != tag)'
