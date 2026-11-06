#!/usr/bin/env bash
# Run the ID-JAG issuer acceptance check locally against a DISPOSABLE PostgreSQL container.
# Never touches your development database: the container is created on a random localhost
# port and removed on exit. Requires docker and `uv` (run `make install` first) and a
# generated ephemeral secret key. Does not load local.env.yml.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
NAME="authentik-mcp-idjag-pg-$$"
export AUTHENTIK_ENV="$NAME"
export AUTHENTIK_SECRET_KEY="$(uv run python -c 'import secrets; print(secrets.token_urlsafe(64))')"
export AUTHENTIK_LOG_LEVEL=warning
# Keep production request logs (which can contain credentials) out of failure output/JUnit.
export PYTEST_ADDOPTS="--tb=short --show-capture=no -o junit_logging=no"
export MCP_CONFORMANCE_RESULTS_DIR="${MCP_CONFORMANCE_RESULTS_DIR:-$ROOT/tests/mcp_conformance_id_jag_issuer/results}"
PASSWORD="$(uv run python -c 'import secrets; print(secrets.token_urlsafe(18))')"

cleanup() { docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT

docker run -d --rm --name "$NAME" \
  -e POSTGRES_USER=authentik -e POSTGRES_PASSWORD="$PASSWORD" -e POSTGRES_DB=authentik \
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
export AUTHENTIK_POSTGRESQL__NAME=authentik
export AUTHENTIK_POSTGRESQL__TEST__NAME=test_authentik_mcp_id_jag_issuer

echo "== fixture self-check"
uv run python tests/mcp_conformance_id_jag_issuer/selfcheck_resource_as.py
echo "== acceptance check (expected to FAIL until the conformance gaps are corrected)"
status=0
uv run manage.py test tests/mcp_conformance_id_jag_issuer/acceptance_id_jag.py || status=$?
echo "== report: $MCP_CONFORMANCE_RESULTS_DIR/report.md"
cat "$MCP_CONFORMANCE_RESULTS_DIR/report.md" 2>/dev/null || true
exit "$status"
