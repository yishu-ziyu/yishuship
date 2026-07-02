#!/usr/bin/env bash
set -u

# yishuship PM init — initialize Product Lifecycle V2 workflow state.
# Usage:
#   bash pm-init.sh [task_description]
#   bash pm-init.sh [cwd] [task_description]
#
# Creates:
#   .ship/pm-state.yaml          — workflow state
#   .ship/tasks/<task_id>/       — V2 product lifecycle task directory

if [ "$#" -eq 1 ] && [ ! -d "${1:-}" ]; then
  CWD="."
  DESC="$1"
else
  CWD="${1:-.}"
  DESC="${2:-}"
fi

TASK_ID=$(date +%Y%m%d-%H%M%S)
TASK_DIR="$CWD/.ship/tasks/$TASK_ID"

mkdir -p "$TASK_DIR"/{input,product,delivery,growth,control,plan,e2e,qa}

cat > "$CWD/.ship/pm-state.yaml" << EOF
phase: product-type
task_id: $TASK_ID
created: $(date -Iseconds)
workflow: product-lifecycle-v2
description: "$DESC"
EOF

if [ -n "$DESC" ]; then
  {
    printf '# Idea\n\n'
    printf '%s\n' "$DESC"
  } > "$TASK_DIR/input/idea.md"
  {
    printf '# Requirement\n\n'
    printf '## Original Input\n\n'
    printf '%s\n' "$DESC"
  } > "$TASK_DIR/input/requirement.md"
fi

cat > "$TASK_DIR/control/run_state.yaml" << EOF
task_id: $TASK_ID
active: true
current_phase: product-type
status: running
workflow: product-lifecycle-v2
updated_at: "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
EOF

echo "PM workflow initialized."
echo "  State: $CWD/.ship/pm-state.yaml"
echo "  Task:  $TASK_DIR"
echo "  Phase: product-type"
