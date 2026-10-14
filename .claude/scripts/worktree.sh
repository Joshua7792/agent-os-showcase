#!/usr/bin/env bash
# Parallel-lane worktrees. `main` in the repo root is the real, working repo.
# A worktree is ONE card's short-lived workspace: created from main, built + tested there, merged back into main,
# then deleted. It lives INSIDE the repo at .worktrees/<name> (gitignored) — never a second copy of the repo elsewhere.
#
#   bash .claude/scripts/worktree.sh new   <name> [--sparse <profile>]  # branch wt/<name> from main at .worktrees/<name>;
#                                                    # full checkout by default; with --sparse, only the paths listed in
#                                                    # .claude/scripts/sparse/<profile>.txt (one /path per line)
#   bash .claude/scripts/worktree.sh list           # every open worktree (also list them in the project todo)
#   bash .claude/scripts/worktree.sh merge <name>   # merge wt/<name> into main (worktree must be committed + clean).
#                                                    # Safety net (from a real incident): refuses if the branch touches a
#                                                    # file main has dirty/untracked, and snapshots main's uncommitted
#                                                    # tracked edits to refs/backup/premerge-<ts>-<name> first.
#   bash .claude/scripts/worktree.sh done  <name>   # unlink node_modules, remove the worktree, delete the merged branch
#
# Optional: WT_NODE_MODULES=<repo-relative app folder> links that folder's node_modules from main into the worktree
# (Windows junction, no reinstall). Rule: shared local services (a database container, a dev server) are used from
# ONE place at a time. `done` refuses to delete an unmerged branch.
set -euo pipefail
R="$(git rev-parse --show-toplevel)"
WT="$R/.worktrees"
APP_REL="${WT_NODE_MODULES:-}"
cmd="${1:-}"; name="${2:-}"

need_name() { [[ "$name" =~ ^[[:lower:][:digit:]][[:lower:][:digit:]._-]*$ ]] || { echo "name: lowercase letters, digits, . _ - (got '$name')" >&2; exit 2; }; }
win() { cygpath -w "$1"; }

case "$cmd" in
  new)
    need_name
    if [ "${3:-}" = "--sparse" ]; then
      profile="${4:-}"
      list="$R/.claude/scripts/sparse/$profile.txt"
      [[ "$profile" =~ ^[[:lower:][:digit:]][[:lower:][:digit:]._-]*$ ]] && [ -f "$list" ] || { echo "no sparse profile '$profile' ($list)" >&2; exit 2; }
      mapfile -t paths < <(sed -e 's/\r$//' -e '/^[[:space:]]*#/d' -e '/^[[:space:]]*$/d' "$list")
      git -C "$R" worktree add --no-checkout -b "wt/$name" "$WT/$name" main
      # MSYS_NO_PATHCONV: Git Bash would otherwise rewrite "/src/..." to "C:/Program Files/Git/src/...".
      MSYS_NO_PATHCONV=1 git -C "$WT/$name" sparse-checkout set --no-cone "${paths[@]}"
      git -C "$WT/$name" reset -q --hard HEAD   # populate (a plain checkout of the same branch is a no-op)
    else
      git -C "$R" worktree add -b "wt/$name" "$WT/$name" main
    fi
    if [ -n "$APP_REL" ] && [ -d "$R/$APP_REL/node_modules" ] && [ -d "$WT/$name/$APP_REL" ]; then
      # A junction, not a copy: the worktree uses main's installed packages (no reinstall, no disk copy).
      powershell -NoProfile -Command "New-Item -ItemType Junction -Path '$(win "$WT/$name/$APP_REL/node_modules")' -Target '$(win "$R/$APP_REL/node_modules")' | Out-Null"
      echo "linked $APP_REL/node_modules -> main's"
    fi
    echo "worktree ready: $WT/$name (branch wt/$name from main $(git -C "$R" rev-parse --short main))"
    ;;
  list)
    git -C "$R" worktree list
    ;;
  merge)
    need_name
    [ "$(git -C "$R" rev-parse --abbrev-ref HEAD)" = "main" ] || { echo "the repo root must have main checked out" >&2; exit 1; }
    if [ -n "$(git -C "$WT/$name" status --porcelain)" ]; then
      echo "worktree $name has uncommitted changes — commit them in the worktree first:" >&2
      git -C "$WT/$name" status --short >&2; exit 1
    fi
    # Safety net: a merge that failed to write .git/index once aborted by resetting every dirty tracked file
    # in main to HEAD, wiping uncommitted work. So: (1) refuse if the branch touches a file main has dirty or
    # untracked; (2) snapshot main's uncommitted tracked edits to a ref first (stash create changes nothing).
    touched="$(git -C "$R" diff --name-only "main...wt/$name")"
    dirty="$(git -C "$R" diff --name-only HEAD; git -C "$R" ls-files --others --exclude-standard)"
    clash="$(comm -12 <(printf '%s\n' "$touched" | sort -u) <(printf '%s\n' "$dirty" | sort -u) | sed '/^$/d')"
    if [ -n "$clash" ]; then
      echo "refusing: wt/$name changes files that main has uncommitted/untracked edits in:" >&2
      printf '  %s\n' "$clash" >&2; exit 1
    fi
    snap="$(git -C "$R" stash create "pre-merge $name")"
    if [ -n "$snap" ]; then
      ref="refs/backup/premerge-$(date +%Y%m%d-%H%M%S)-$name"
      git -C "$R" update-ref "$ref" "$snap"
      echo "main's uncommitted edits snapshotted to $ref (restore a file: git checkout $ref -- <path>)"
    fi
    if ! git -C "$R" merge --no-ff "wt/$name" -m "merge(wt): $name into main"; then
      echo "MERGE FAILED. Do not retry blindly. Check 'git status'; if edits vanished: git checkout ${ref:-<no snapshot>} -- <path>" >&2
      exit 1
    fi
    echo "merged wt/$name into main — run the card's gate on main before 'done'"
    ;;
  done)
    need_name
    if [ -n "$APP_REL" ]; then
      J="$WT/$name/$APP_REL/node_modules"
      # Remove the JUNCTION first (rmdir on a junction deletes the link only), so removing the worktree can never
      # reach through it into main's node_modules.
      if [ -e "$J" ]; then cmd //c rmdir "$(win "$J")"; fi
    fi
    git -C "$R" worktree remove "$WT/$name"
    git -C "$R" branch -d "wt/$name"   # -d (not -D): refuses if the branch was never merged
    git -C "$R" worktree prune
    echo "removed worktree $name and branch wt/$name"
    ;;
  *)
    sed -n '2,17p' "$0"; exit 2
    ;;
esac
