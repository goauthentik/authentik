#!/usr/bin/env bash
# Stack pane: authentik against the stack's database. Migrates, starts Django's development
# server (`manage.py dev_server`, no Rust binary or web build needed), configures both ID-JAG
# roles once (stack/bootstrap.py writes .stack/config.json), then stays in the foreground.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
load_env
cd "$ROOT"

wait_for "PostgreSQL" docker exec "$STACK_CONTAINER" pg_isready -U "$AUTHENTIK_POSTGRESQL__USER" -h 127.0.0.1
echo "== migrate"
uv run python -m lifecycle.migrate

echo "== authentik on http://localhost:$STACK_AK_PORT"
uv run manage.py dev_server "127.0.0.1:$STACK_AK_PORT" &
server=$!
trap 'kill "$server" 2>/dev/null || true' EXIT INT TERM

wait_for "authentik" curl -fsS "http://localhost:$STACK_AK_PORT/-/health/live/"
if [[ ! -f "$CONFIG" ]]; then
  echo "== configure both ID-JAG roles"
  uv run python "$SUITE/stack/bootstrap.py"
fi
echo "== ready (configuration: $CONFIG)"
wait "$server"
