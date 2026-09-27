# This folder is a fresh project with no ideas; another registered project has one waiting.
source "$(dirname "$0")/../../fixtures/setup.sh"
cases="$(cd "$(dirname "$0")/.." && pwd)"
start todo
finish
other="$(mktemp -d)/work-todo"
mkdir -p "$other"
( cd "$other" && bash "$cases/continue-ask/scaffold.sh" )
mkdir -p "$YISHUSHIP_HOME"
printf '%s\n' "$other" > "$YISHUSHIP_HOME/projects"
