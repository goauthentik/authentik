#!/usr/bin/env bash
# Start a fresh, long-running ID-JAG end-to-end stack in a Rex session, one pane per component:
#
#   +----------------------------+-----------------------------------+
#   | postgres (disposable)      | authentik: migrate, configure     |
#   |                            | both roles, serve                 |
#   +----------------------------+-----------------------------------+
#   | client: the MCP SDK        | MCP server (server SDK), logs     |
#   | harness, then a shell      | every request it authorizes       |
#   +----------------------------+-----------------------------------+
#
# Every run gets a new database container, ephemeral secret key and new credentials, kept
# in tests/mcp_conformance_id_jag_mcp_client/.stack/ (gitignored, mode 0700). Stop it with
# stack/down.sh. Requires the Rex app, docker, uv (`make install`), Node 24 and pnpm.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
REX="$(rex_bin)"
STACK="$SUITE/stack"

if [[ -f "$ENV_FILE" ]]; then
  echo "a stack already exists ($STATE): stop it with stack/down.sh first" >&2
  exit 1
fi

echo "== harness dependencies (node $(node --version))"
pnpm --dir "$SUITE" install --frozen-lockfile --silent

free_port() {
  uv run python -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])'
}
token() {
  uv run python -c "import secrets; print(secrets.token_urlsafe($1))"
}

pg_port="$(free_port)"
mkdir -p "$STATE"
chmod 700 "$STATE"
umask 077
cat >"$ENV_FILE" <<EOF
STACK_CONTAINER=authentik-mcp-idjag-e2e-pg-$$
STACK_AK_PORT=$(free_port)
STACK_MCP_PORT=$(free_port)
STACK_HARNESS_MCP_PORT=$(free_port)
AUTHENTIK_ENV=authentik-mcp-idjag-e2e-$$
AUTHENTIK_SECRET_KEY=$(token 64)
AUTHENTIK_DEBUG=true
AUTHENTIK_LOG_LEVEL=info
AUTHENTIK_BLUEPRINTS_DIR=$ROOT/blueprints
AUTHENTIK_POSTGRESQL__HOST=127.0.0.1
AUTHENTIK_POSTGRESQL__PORT=$pg_port
AUTHENTIK_POSTGRESQL__USER=authentik
AUTHENTIK_POSTGRESQL__PASSWORD=$(token 18)
AUTHENTIK_POSTGRESQL__NAME=authentik_mcp_id_jag_e2e
AUTHENTIK_POSTGRESQL__TEST__NAME=test_authentik_mcp_id_jag_e2e
EOF

created="$("$REX" new "$SESSION_LABEL" --window Stack -c "$ROOT" --keep-open --json -- "$STACK/postgres.sh")"
session="$(printf '%s' "$created" | jq -er '.session_id')"
pg_block="$(printf '%s' "$created" | jq -er '.initial_windows[0].block_ids[0]')"
echo "STACK_REX_SESSION=$session" >>"$ENV_FILE"

ak_block="$("$REX" split -s "$session" -b "$pg_block" --split=right --ratio 60 --label authentik \
  -c "$ROOT" --keep-open --focus=false --json -- "$STACK/authentik.sh" | jq -er '.block_ids[0]')"
"$REX" split -s "$session" -b "$ak_block" --split=below --label "MCP server" \
  -c "$ROOT" --keep-open --focus=false --json -- "$STACK/mcp-server.sh" >/dev/null
# The client runs once, then leaves a shell for reruns
"$REX" split -s "$session" -b "$pg_block" --split=below --label client -c "$ROOT" --json \
  -- bash -c '"$0"; exec "${SHELL:-/bin/zsh}" -l' "$STACK/client.sh" >/dev/null

echo "== started Rex session $SESSION_LABEL ($session)"
echo "   state:  $STATE (credentials in config.json, mode 0600)"
echo "   stop:   tests/mcp_conformance_id_jag_mcp_client/stack/down.sh"
