#!/usr/bin/env bash
# Run the ID-JAG MCP client (official MCP TypeScript SDK) acceptance check locally against a
# DISPOSABLE PostgreSQL container. Never touches your development database: the container is
# created on a random localhost port and removed on exit. Requires docker, `uv` (run
# `make install` first), Node 24 and pnpm, and a generated ephemeral secret key. Does not load
# local.env.yml.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SUITE="$ROOT/tests/mcp_conformance_id_jag_mcp_client"
cd "$ROOT"

# Prefer nvm's Node 24.22.2 when present; otherwise use the Node on PATH.
NVM_NODE="${NVM_DIR:-$HOME/.nvm}/versions/node/v24.22.2/bin"
if [[ -x "$NVM_NODE/node" ]]; then
  export PATH="$NVM_NODE:$PATH"
fi
export MCP_CLIENT_NODE="$(command -v node)"
echo "== harness dependencies (node $(node --version))"
pnpm --dir "$SUITE" install --frozen-lockfile --silent

NAME="authentik-mcp-idjag-mcp-client-pg-$$"
export AUTHENTIK_ENV="$NAME"
export AUTHENTIK_SECRET_KEY="$(uv run python -c 'import secrets; print(secrets.token_urlsafe(64))')"
export AUTHENTIK_LOG_LEVEL=warning
# Override the repository full-trace default, which prints credential-bearing arguments.
# Keep production request logs and local variables out of failure output/JUnit.
export PYTEST_ADDOPTS="-o addopts= -p authentik.root.test_plugin --junitxml=unittest.xml --tb=short --no-showlocals --show-capture=no -o junit_logging=no"
export MCP_CONFORMANCE_RESULTS_DIR="${MCP_CONFORMANCE_RESULTS_DIR:-$SUITE/results/$(date -u +%Y%m%dT%H%M%SZ)-$$}"
mkdir -p "$MCP_CONFORMANCE_RESULTS_DIR"
if [[ -e "$MCP_CONFORMANCE_RESULTS_DIR/report.json" ]]; then
  echo "Choose a fresh MCP_CONFORMANCE_RESULTS_DIR; an earlier report already exists." >&2
  exit 1
fi
PASSWORD="$(uv run python -c 'import secrets; print(secrets.token_urlsafe(18))')"

cleanup() { docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT

docker run -d --rm --name "$NAME" \
  -e POSTGRES_USER=authentik -e POSTGRES_PASSWORD="$PASSWORD" -e POSTGRES_DB=authentik_mcp_id_jag_mcp_client \
  -p 127.0.0.1::5432 docker.io/library/postgres:16 >/dev/null
PORT="$(docker port "$NAME" 5432/tcp | head -n1 | sed 's/.*://')"
for _ in $(seq 1 60); do
  docker exec "$NAME" pg_isready -U authentik -h 127.0.0.1 >/dev/null 2>&1 && break
  sleep 1
done
docker exec "$NAME" pg_isready -U authentik -h 127.0.0.1 >/dev/null

export AUTHENTIK_POSTGRESQL__HOST=127.0.0.1
export AUTHENTIK_POSTGRESQL__PORT="$PORT"
export AUTHENTIK_POSTGRESQL__USER=authentik
export AUTHENTIK_POSTGRESQL__PASSWORD="$PASSWORD"
export AUTHENTIK_POSTGRESQL__NAME=authentik_mcp_id_jag_mcp_client
export AUTHENTIK_POSTGRESQL__TEST__NAME=test_authentik_mcp_id_jag_mcp_client

echo "== fixture self-check (MCP server fixture and SDK client, independent of authentik)"
pnpm --dir "$SUITE" run --silent selfcheck
echo "== acceptance check"
status=0
uv run manage.py test tests/mcp_conformance_id_jag_mcp_client/acceptance_mcp_client.py || status=$?
echo "== report: $MCP_CONFORMANCE_RESULTS_DIR/report.md"
cat "$MCP_CONFORMANCE_RESULTS_DIR/report.md" 2>/dev/null || true
exit "$status"
