#!/usr/bin/env bash
# End-to-end test of .claude/scripts/worktree.sh in a throwaway repo under $TMPDIR.
# Covers: full and sparse lanes, the dirty-main clash refusal, the premerge snapshot ref, merge, done.
#   bash scripts/test-worktree.sh
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT
fail() { echo "FAIL: $*" >&2; exit 1; }
ok() { echo "ok   $*"; }

cd "$T"
git init -q -b main .
git config user.email test@example.com
git config user.name test
mkdir -p .claude/scripts/sparse tools tasks/example-project other
cp "$HERE/.claude/scripts/worktree.sh" .claude/scripts/
cp "$HERE/.claude/scripts/sparse/example.txt" .claude/scripts/sparse/
printf '.worktrees/\n' > .gitignore
echo a > tools/a.txt; echo t > tasks/example-project/todo.md; echo o > other/o.txt
printf '# agents\n' > AGENTS.md; printf '@AGENTS.md\n' > CLAUDE.md
git add -A && git commit -qm init
W=".claude/scripts/worktree.sh"

# full lane
bash "$W" new lane-a >/dev/null
[ -f .worktrees/lane-a/other/o.txt ] || fail "full lane missing other/o.txt"
ok "new (full) checks out everything"

# sparse lane
bash "$W" new lane-b --sparse example >/dev/null
[ -f .worktrees/lane-b/tools/a.txt ] || fail "sparse lane missing tools/a.txt"
[ ! -e .worktrees/lane-b/other/o.txt ] || fail "sparse lane should not contain other/"
ok "new --sparse checks out only the profile's paths"

# bad names and profiles are refused
if bash "$W" new Bad_Name 2>/dev/null; then fail "uppercase name accepted"; fi
if bash "$W" new lane-c --sparse nope 2>/dev/null; then fail "missing profile accepted"; fi
ok "bad lane name and unknown profile refused"

# lane commits a change to tools/a.txt
echo lane > .worktrees/lane-a/tools/a.txt
git -C .worktrees/lane-a commit -qam "lane change"

# main has an uncommitted edit to the SAME file -> merge must refuse
echo dirty > tools/a.txt
if bash "$W" merge lane-a 2>/dev/null; then fail "merge accepted a clash with dirty main"; fi
ok "merge refuses when main has uncommitted edits in a file the lane touched"
git checkout -q -- tools/a.txt

# main has an unrelated uncommitted edit -> merge proceeds and snapshots it first
echo dirty-other > other/o.txt
out="$(bash "$W" merge lane-a)"
echo "$out" | grep -q "snapshotted to refs/backup/premerge-" || fail "no premerge snapshot reported"
git for-each-ref refs/backup | grep -q premerge- || fail "no refs/backup/premerge-* ref"
[ "$(cat other/o.txt)" = "dirty-other" ] || fail "main's unrelated edit was lost"
[ "$(cat tools/a.txt)" = "lane" ] || fail "lane change not merged"
git log -1 --format=%s | grep -q "^merge(wt): lane-a into main$" || fail "merge commit message"
ok "merge snapshots main's edits, keeps them, and merges the lane"

# done removes the worktree and the merged branch; an unmerged branch is protected
bash "$W" done lane-a >/dev/null
[ ! -d .worktrees/lane-a ] || fail "worktree dir still exists"
! git show-ref -q --verify refs/heads/wt/lane-a || fail "merged branch not deleted"
echo x > .worktrees/lane-b/tools/new.txt
git -C .worktrees/lane-b add -A && git -C .worktrees/lane-b commit -qm "unmerged"
if bash "$W" done lane-b 2>/dev/null; then fail "done deleted an unmerged branch"; fi
git show-ref -q --verify refs/heads/wt/lane-b || fail "unmerged branch was deleted"
ok "done cleans up merged lanes and refuses to delete an unmerged branch"

echo "PASS: worktree.sh (6 checks)"
