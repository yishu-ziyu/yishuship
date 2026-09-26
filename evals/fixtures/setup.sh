# Sourced by each case's scaffold.sh, which runs in the empty workspace.
#   start <fixture>        copy a fixture project here and make the first commit
#   finish                 commit whatever the case added and tag it `base`
set -euo pipefail
FIXTURES="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
git_() { git -c user.name=me -c user.email=me@example.com "$@"; }
start() { cp -R "$FIXTURES/$1/." .; git init -q; git_ add -A; git_ commit -qm "init"; }
finish() { git_ add -A; git_ commit -qm "${1:-docs: progress files}" --allow-empty; git tag base; }
