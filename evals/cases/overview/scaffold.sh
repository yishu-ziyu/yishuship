# Two registered projects; the command is typed from a folder that is not a project.
set -euo pipefail
cases="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p home-todo work-todo
( cd home-todo && bash "$cases/continue-ask/scaffold.sh" )
( cd work-todo && bash "$cases/continue-reconcile/scaffold.sh" )
mkdir -p "$YISHUSHIP_HOME"
printf '%s\n' "$PWD/home-todo" "$PWD/work-todo" > "$YISHUSHIP_HOME/projects"
