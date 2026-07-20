#!/usr/bin/env bash
# Run a single `mike ... --push` command with fetch-reset-retry so a concurrent
# gh-pages push (non-fast-forward) self-heals instead of failing the deploy.
#
# Why this is needed: mike never runs `git fetch` itself. It synthesises the
# version commit from the *local* gh-pages ref (via git fast-import) and does a
# fast-forward-only `git push` with no retry. If the real remote gh-pages has
# advanced since that local ref was last updated (a concurrent deploy, or an
# out-of-band push such as a history squash), the push is rejected
# (`! [rejected] gh-pages -> gh-pages (fetch first)`) and the job dies.
#
# Before each attempt we fetch the real remote tip and hard-reset the local
# branch to it, so mike rebuilds on the current tip. mike merges versions.json
# from the tip it builds on, so concurrently-added versions are preserved and a
# retry is idempotent. The hard reset each attempt also discards any commit a
# failed prior attempt left on the local ref, avoiding mike's GitBranchDiverged
# pre-flight abort.
#
# Env:
#   PACKAGE_MANAGER    pip | uv | pixi. "pip" runs mike directly; others prefix
#                      the command with "<pm> run".
#   MIKE_REMOTE        git remote to push to (default: origin).
#   MIKE_BRANCH        docs branch mike manages (default: gh-pages).
#   MIKE_MAX_ATTEMPTS  number of attempts before giving up (default: 5).
#
# Args: the mike subcommand and its flags, e.g.
#   mike_push.sh deploy --push develop
#   mike_push.sh set-default --push main
set -uo pipefail

PACKAGE_MANAGER="${PACKAGE_MANAGER:-pip}"
REMOTE="${MIKE_REMOTE:-origin}"
BRANCH="${MIKE_BRANCH:-gh-pages}"
MAX_ATTEMPTS="${MIKE_MAX_ATTEMPTS:-5}"

if [ "$#" -eq 0 ]; then
  echo "::error::mike_push.sh requires a mike subcommand (e.g. deploy --push develop)"
  exit 2
fi

if [ "$PACKAGE_MANAGER" = "pip" ]; then
  MIKE=(mike)
else
  MIKE=("$PACKAGE_MANAGER" run mike)
fi

# Point the local docs branch at the current remote tip so mike rebuilds on it.
# A missing remote branch (first-ever deploy) is fine: mike creates it fresh.
sync_local_branch() {
  if git fetch "$REMOTE" "$BRANCH" 2>/dev/null; then
    git branch -f "$BRANCH" FETCH_HEAD 2>/dev/null || true
  else
    echo "note: $REMOTE/$BRANCH not found yet (first deploy?); mike will create it"
  fi
}

attempt=1
while [ "$attempt" -le "$MAX_ATTEMPTS" ]; do
  sync_local_branch
  if "${MIKE[@]}" "$@"; then
    exit 0
  fi
  echo "::warning::mike $* was rejected (attempt ${attempt}/${MAX_ATTEMPTS}); refetching ${REMOTE}/${BRANCH} and retrying"
  sleep "$(( attempt * 3 ))"
  attempt=$(( attempt + 1 ))
done

echo "::error::mike $* failed after ${MAX_ATTEMPTS} attempts (gh-pages push kept getting rejected)"
exit 1
