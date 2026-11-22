#!/usr/bin/env bash
# Authenticate the gh-pages push with the mkdocs-deploy `deploy-token` input
# (passed in as ACTIONS_DEPLOY_TOKEN).
#
# Why this exists: mike's `git push` uses whatever git credentials are ambient.
# Without this step the deploy silently rode on the credential actions/checkout
# persisted, and the deploy-token input did nothing. Here we install an
# http.<host>.extraheader built from the token and --replace-all any credential
# checkout left at the same key, so the input genuinely controls who publishes
# the docs (and a scoped token for a different repo becomes possible).
#
# Scope and safety:
#   * Only an https GitHub remote is touched. A non-GitHub or file:// origin
#     (the test harness reroutes origin to file:///tmp/fake-remote.git) is left
#     untouched, so that push keeps working with no auth. An ssh origin is also
#     left alone — the extraheader only applies to https.
#   * Only the local repo config is written; the Actions runner is ephemeral.
#   * The derived Basic-auth value is masked so it never appears in the log.
#
# Env:
#   ACTIONS_DEPLOY_TOKEN  the deploy-token value (required for wiring).
#   GITHUB_SERVER_URL     GitHub base URL (default https://github.com); set by
#                         Actions, and distinct on GitHub Enterprise Server.
set -uo pipefail

TOKEN="${ACTIONS_DEPLOY_TOKEN:-}"
if [ -z "$TOKEN" ]; then
  echo "::warning::deploy-token is empty; leaving existing git credentials in place"
  exit 0
fi

origin_url="$(git remote get-url origin 2>/dev/null || true)"
server_url="${GITHUB_SERVER_URL:-https://github.com}"
host_prefix="${server_url%/}/"   # e.g. https://github.com/

case "$origin_url" in
  "${host_prefix}"*)
    # HTTP Basic auth: username x-access-token, password = the token. "tr -d"
    # strips the line wrapping base64 adds on some platforms.
    auth_b64="$(printf 'x-access-token:%s' "$TOKEN" | base64 | tr -d '\n')"
    echo "::add-mask::${auth_b64}"
    git config --local --replace-all "http.${host_prefix}.extraheader" "AUTHORIZATION: basic ${auth_b64}"
    echo "Configured gh-pages push auth from deploy-token for ${host_prefix}"
    ;;
  *)
    echo "origin (${origin_url:-<none>}) is not a ${host_prefix} remote; using existing credentials"
    ;;
esac
