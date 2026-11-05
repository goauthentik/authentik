#!/usr/bin/env bash
# PROTOTYPE (01b), never merge: start the CIMD probe.
#
#   scripts/cimd-prototype/run.sh authentik   # terminal 1: server + worker on :9000
#   scripts/cimd-prototype/run.sh mcp         # terminal 2: protected MCP server on :8765
#   scripts/cimd-prototype/run.sh tail        # terminal 3: live view of OAuth traffic
#   scripts/cimd-prototype/run.sh new-run X   # archive logs, start a fresh run named X
#   scripts/cimd-prototype/run.sh summary [X] # summarize the current (or archived) run
#   scripts/cimd-prototype/run.sh password    # print the akadmin password
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
STATE="${CIMD_PROTOTYPE_STATE:-/tmp/cimd-prototype}"
SLUG=mcp-proto
mkdir -p "$STATE"
cd "$ROOT"

if [ ! -s "$STATE/akadmin-password" ]; then
  (umask 077 && python3 -c "import secrets; print(secrets.token_urlsafe(16))" > "$STATE/akadmin-password")
fi

export AUTHENTIK_POSTGRESQL__NAME=authentik_cimd
export AUTHENTIK_WEB__BASE_URL=http://localhost:9000
export AUTHENTIK_LISTEN__HTTP='127.0.0.1:9000,[::1]:9000'
export AUTHENTIK_LISTEN__HTTPS='127.0.0.1:9443,[::1]:9443'
export AUTHENTIK_LISTEN__METRICS='127.0.0.1:9300,[::1]:9300'
export AUTHENTIK_LISTEN__DEBUG=127.0.0.1:9900
export AUTHENTIK_LISTEN__DEBUG_PY=127.0.0.1:9901
export AUTHENTIK_LISTEN__DEBUG_TOKIO='[::1]:6669'
export AUTHENTIK_BOOTSTRAP_PASSWORD="$(cat "$STATE/akadmin-password")"
export AUTHENTIK_BOOTSTRAP_EMAIL=akadmin@localhost.invalid
export AUTHENTIK_CIMD_PROTOTYPE__APPLICATIONS=$SLUG
export AUTHENTIK_CIMD_PROTOTYPE__LOG="$STATE/requests.jsonl"
export AUTHENTIK_CIMD_PROTOTYPE__ALLOW_HTTP_LOCALHOST=true
# macOS: forked gunicorn workers crash once the Objective-C runtime is initialized
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
export NO_PROXY="*"
# Reuse the main checkout's Rust build, if there is one
if [ -z "${CARGO_TARGET_DIR:-}" ] && [ -d "$HOME/workspaces/authentik/target" ]; then
  export CARGO_TARGET_DIR="$HOME/workspaces/authentik/target"
fi

wait_ready() {
  for _ in $(seq 1 120); do
    [ "$(curl -s -o /dev/null -w '%{http_code}' http://localhost:9000/-/health/ready/ || true)" = 200 ] && return 0
    sleep 2
  done
  echo "authentik did not become ready on :9000" >&2
  return 1
}

client_id() {
  # Idempotent: creates the provider and application on first use
  for _ in $(seq 1 30); do
    out=$(uv run manage.py shell -c "exec(open('scripts/cimd-prototype/setup_provider.py').read())" 2>/dev/null | grep '^client_id:' || true)
    if [ -n "$out" ]; then
      echo "${out#client_id: }"
      return 0
    fi
    sleep 5 # default flows are still being created by blueprints
  done
  echo "could not create the prototype provider" >&2
  return 1
}

case "${1:-}" in
  authentik)
    if ! docker exec postgres psql -U postgres -Atc "select 1 from pg_database where datname='authentik_cimd'" | grep -q 1; then
      docker exec postgres createdb -U postgres authentik_cimd
    fi
    exec uv run ak allinone
    ;;
  mcp)
    wait_ready
    id=$(client_id)
    echo "provider client_id: $id"
    exec uv run scripts/cimd-prototype/mcp_server.py \
      --issuer "http://localhost:9000/application/o/$SLUG/" --audience "$id"
    ;;
  tail)
    touch "$STATE/requests.jsonl"
    tail -n 0 -F "$STATE/requests.jsonl" | jq -c --unbuffered '
      if .kind == "http" then
        {t: .ts[11:19], req: "\(.method) \(.path)", status,
         client_id: (.query.client_id // .form.client_id),
         grant: .form.grant_type, resource: (.query.resource // .form.resource),
         pkce: .query.code_challenge_method, refresh_token: .form.refresh_token.sha,
         error: .response.error, ua: .headers["User-Agent"]}
      else {t: .ts[11:19], kind, client_id, status, matched, redirect_uri, error, reason}
      end | with_entries(select(.value != null))'
    ;;
  new-run)
    name="${2:?usage: run.sh new-run <name, e.g. claude-code>}"
    # Keep whatever was logged before, without mixing it into the new run
    if [ -s "$STATE/requests.jsonl" ] || [ -s "$STATE/mcp.jsonl" ]; then
      old="$STATE/runs/_unsaved-$(date +%Y%m%d-%H%M%S)"
      mkdir -p "$old"
      mv "$STATE/requests.jsonl" "$STATE/mcp.jsonl" "$old/" 2>/dev/null || true
      echo "Moved previous logs to $old"
    fi
    : > "$STATE/requests.jsonl"
    : > "$STATE/mcp.jsonl"
    echo "$name" > "$STATE/current-run"
    echo "Fresh logs for run '$name'. Summarize with: scripts/cimd-prototype/run.sh summary"
    ;;
  summary)
    if [ -n "${2:-}" ]; then
      exec python3 scripts/cimd-prototype/summarize.py "$STATE/runs/$2"
    fi
    exec python3 scripts/cimd-prototype/summarize.py "$STATE"
    ;;
  save)
    name="${2:-$(cat "$STATE/current-run" 2>/dev/null || true)}"
    name="${name:?usage: run.sh save <name>}"
    mkdir -p "$STATE/runs/$name"
    cp "$STATE/requests.jsonl" "$STATE/mcp.jsonl" "$STATE/runs/$name/" 2>/dev/null || true
    python3 scripts/cimd-prototype/summarize.py "$STATE/runs/$name" > "$STATE/runs/$name/summary.md"
    echo "Saved to $STATE/runs/$name (summary.md, requests.jsonl, mcp.jsonl)"
    ;;
  password)
    cat "$STATE/akadmin-password"
    ;;
  *)
    sed -n '2,10p' "$0"
    exit 1
    ;;
esac
