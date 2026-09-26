---
type: command
---
# Deterministic: on the files as they were before the run, the status line must say a review is due.
t=$(mktemp -d); mkdir -p "$t/.ship/ideas"
git show base:.ship/ideas/due-sort.md > "$t/.ship/ideas/due-sort.md"
python3 "$EVAL_PLUGIN/scripts/ideas.py" --status-line "$t" | grep -q '回头看'
