# Rebase Safety Gate

Use this only when an already-pushed PR branch may need rebase.

Default to **not safe** if any command fails, returns ambiguous output, or shows
human collaboration.

```bash
BRANCH=$(git branch --show-current)
BASE=$(gh pr view "$BRANCH" --json baseRefName --jq '.baseRefName')
PR_AUTHOR=$(gh pr view "$BRANCH" --json author --jq '.author.login')
ME=$(gh api user --jq '.login')
export PR_AUTHOR ME

# 1. Agent-owned branch naming convention.
case "$BRANCH" in
  yishuship/*|ship/*|codex/*) echo "agent-owned-name" ;;
  *) echo "NOT_SAFE: branch name is not agent-owned"; exit 1 ;;
esac

# 2. No human approvals, change requests, comments, or review threads.
gh pr view "$BRANCH" --json reviews,comments --jq '
  [
    .reviews[]?.author.login,
    .comments[]?.author.login
  ]
  | map(select(. != "github-actions[bot]" and . != "dependabot[bot]"))
  | map(select(. != env.PR_AUTHOR and . != env.ME))
  | length == 0
' || { echo "NOT_SAFE: human review/comment signal"; exit 1; }

# 3. No unresolved review threads from humans.
OWNER=$(gh repo view --json owner --jq '.owner.login')
REPO=$(gh repo view --json name --jq '.name')
PR_NUMBER=$(gh pr view "$BRANCH" --json number --jq '.number')
gh api graphql -f owner="$OWNER" -f repo="$REPO" -F number="$PR_NUMBER" -f query='
query($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      reviewThreads(first: 100) {
        nodes {
          isResolved
          comments(first: 20) {
            nodes { author { login } }
          }
        }
      }
    }
  }
}' --jq '
  [
    .data.repository.pullRequest.reviewThreads.nodes[]?
    | select(.isResolved == false)
    | .comments.nodes[]?.author.login
  ]
  | map(select(. != "github-actions[bot]" and . != "dependabot[bot]"))
  | map(select(. != env.PR_AUTHOR and . != env.ME))
  | length == 0
' || { echo "NOT_SAFE: unresolved human review thread"; exit 1; }

# 4. No other commit authors on this PR branch.
git fetch origin "$BASE"
MY_EMAIL=$(git config user.email)
UNEXPECTED_AUTHORS=$(git log --format='%ae' "origin/$BASE..HEAD" | \
  sort -u | grep -vxF "$MY_EMAIL" || true)
[ -z "$UNEXPECTED_AUTHORS" ] || {
  echo "NOT_SAFE: unexpected commit authors: $UNEXPECTED_AUTHORS"
  exit 1
}

# 5. Repo appears to prefer/require linear history.
OWNER=$(gh repo view --json owner --jq '.owner.login')
REPO=$(gh repo view --json name --jq '.name')
gh api "repos/$OWNER/$REPO" --jq '
  (.allow_rebase_merge == true or .allow_squash_merge == true)
  and (.allow_merge_commit == false)
' || { echo "NOT_SAFE: repo does not clearly require linear history"; exit 1; }
```

Only when all gates are proven safe may the agent run:

```bash
git rebase "origin/$BASE"
<relevant local verification command>
git push --force-with-lease
```
