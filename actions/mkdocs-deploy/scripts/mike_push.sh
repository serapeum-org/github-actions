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
# Before each attempt we fetch the real remote tip and repoint the local branch
# ref (git branch -f) at it, so mike rebuilds on the current tip. mike merges
# versions.json from the tip it builds on, so concurrently-added versions are
# preserved and a retry is idempotent. Repointing the ref each attempt also
# discards any commit a failed prior attempt left on the local branch, avoiding
# mike's GitBranchDiverged pre-flight abort.
#
# Env:
#   PACKAGE_MANAGER    pip | uv | pixi. "pip" runs mike directly; others prefix
#                      the command with "<pm> run".
#   MIKE_REMOTE        git remote to push to (default: origin).
#   MIKE_BRANCH        docs branch mike manages (default: gh-pages).
#   MIKE_MAX_ATTEMPTS  number of attempts before giving up (default: 5).
#   MIKE_RETRY_BACKOFF base seconds for the linear backoff between attempts
#                      (default: 3; the nth retry sleeps n * this).
#
# Args: the mike subcommand and its flags, e.g.
#   mike_push.sh deploy --push develop
#   mike_push.sh set-default --push main
set -uo pipefail

PACKAGE_MANAGER="${PACKAGE_MANAGER:-pip}"
REMOTE="${MIKE_REMOTE:-origin}"
BRANCH="${MIKE_BRANCH:-gh-pages}"
MAX_ATTEMPTS="${MIKE_MAX_ATTEMPTS:-5}"
BACKOFF="${MIKE_RETRY_BACKOFF:-3}"

# Guard non-integer overrides: a non-numeric MAX_ATTEMPTS makes the loop guard
# error out so mike never runs, and a non-numeric BACKOFF aborts the arithmetic
# under `set -u`. Coerce a bad value back to the default with a clear warning.
case "$MAX_ATTEMPTS" in
  ''|*[!0-9]*) echo "::warning::MIKE_MAX_ATTEMPTS='${MAX_ATTEMPTS}' is not a positive integer; using 5"; MAX_ATTEMPTS=5 ;;
esac
# Force base 10 so a leading-zero value (e.g. 010, 08) isn't parsed as octal in
# the arithmetic contexts below.
MAX_ATTEMPTS=$((10#$MAX_ATTEMPTS))
if [ "$MAX_ATTEMPTS" -lt 1 ]; then
  echo "::warning::MIKE_MAX_ATTEMPTS must be >= 1; using 5"
  MAX_ATTEMPTS=5
fi
case "$BACKOFF" in
  ''|*[!0-9]*) echo "::warning::MIKE_RETRY_BACKOFF='${BACKOFF}' is not a non-negative integer; using 3"; BACKOFF=3 ;;
esac
BACKOFF=$((10#$BACKOFF))

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
# Distinguish the three cases explicitly instead of treating any git failure as
# "first deploy": remote branch absent (fine — mike creates it), remote
# unreachable (surface it, don't hide auth/network errors), and a reset that
# could not be applied (warn — a stale local ref would make every retry fail).
sync_local_branch() {
  local ls_rc
  git ls-remote --exit-code "$REMOTE" "refs/heads/$BRANCH" >/dev/null 2>&1
  ls_rc=$?
  if [ "$ls_rc" -eq 2 ]; then
    echo "note: $REMOTE/$BRANCH does not exist yet (first deploy); mike will create it"
    return 0
  fi
  if [ "$ls_rc" -ne 0 ]; then
    echo "::warning::could not reach $REMOTE to check $BRANCH (git ls-remote exit $ls_rc); building on the local ref"
    return 0
  fi
  if ! git fetch "$REMOTE" "$BRANCH"; then
    echo "::warning::git fetch of $REMOTE/$BRANCH failed; building on the local ref"
    return 0
  fi
  if ! git branch -f "$BRANCH" FETCH_HEAD; then
    echo "::warning::could not repoint local $BRANCH to the fetched tip (is it checked out?); mike may build on a stale ref"
  fi
}

# Only a non-fast-forward push rejection is worth retrying; auth/permission
# failures, a protected branch, a rejected server hook, a bad version, or a
# missing dependency never self-heal, so fail fast on them. Require BOTH a git
# push-rejection anchor AND the non-fast-forward reason in the captured output.
# The anchor stops a non-ff phrase that only appears in the mkdocs build portion
# of the log (docs content, a plugin line) from flipping an unrelated failure
# into a retried "race"; the reason stops a generic push failure (auth, 403,
# hook) — which carries the anchor but no non-ff reason — from being retried to
# exhaustion. This relies on mike forwarding git's push stderr verbatim (true
# for mike 2.x); the unit tests exercise this matcher against representative and
# captured-real git rejection text, but not mike's actual relay, so a future
# mike that buffers or reformats git output could make it false-negative.
is_push_race() {
  grep -qiE '! \[rejected\]|error: failed to push' "$1" \
    && grep -qiE 'fetch first|non-fast-forward|updates were rejected' "$1"
}

attempt=1
while [ "$attempt" -le "$MAX_ATTEMPTS" ]; do
  sync_local_branch
  out="$(mktemp)"
  # Force English git push-rejection text (so is_push_race matches) WITHOUT
  # forcing an ASCII build. LC_ALL=C would suppress Python's UTF-8 mode — CPython
  # skips PEP 538 coercion and PEP 540 UTF-8 mode whenever LC_ALL is set — which
  # breaks non-ASCII mkdocs builds. Instead: unset any inherited LC_ALL (it would
  # otherwise override LC_MESSAGES), set LC_MESSAGES=C for English git output,
  # and PYTHONUTF8=1 so mike's in-process mkdocs build always handles UTF-8.
  if env -u LC_ALL LC_MESSAGES=C PYTHONUTF8=1 "${MIKE[@]}" "$@" 2>&1 | tee "$out"; then
    rm -f "$out"
    exit 0
  fi
  if ! is_push_race "$out"; then
    rm -f "$out"
    echo "::error::mike $* failed with a non-retryable error (see log above)"
    exit 1
  fi
  rm -f "$out"
  if [ "$attempt" -lt "$MAX_ATTEMPTS" ]; then
    echo "::warning::mike $* lost a gh-pages push race (attempt ${attempt}/${MAX_ATTEMPTS}); refetching ${REMOTE}/${BRANCH} and retrying"
    sleep "$(( attempt * BACKOFF ))"
  fi
  attempt=$(( attempt + 1 ))
done

echo "::error::mike $* still rejected after ${MAX_ATTEMPTS} attempts (gh-pages kept advancing under us)"
exit 1
