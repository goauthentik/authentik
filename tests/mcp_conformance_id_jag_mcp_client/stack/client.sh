#!/usr/bin/env bash
# Stack pane, and the command to rerun from it: the official MCP SDK client end to end
# (harness/run.mjs, every check) against the stack's authentik. The harness starts its own
# copy of the MCP server on a second registered port, so the long-running one in the next pane
# stays free for other clients. Each run writes to a fresh results/<timestamp>-stack/.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
load_env
cd "$SUITE"

wait_for "authentik to be configured" test -f "$CONFIG"
results="$SUITE/results/$(date -u +%Y%m%dT%H%M%SZ)-stack"
mkdir -p "$results"

version() { node -p "require('./node_modules/$1/package.json').version"; }
# Secrets go over stdin, never argv or the environment
node -e '
const fs = require("node:fs");
const [config, results, port, client, server, oidc, jose] = process.argv.slice(1);
const c = JSON.parse(fs.readFileSync(config, "utf8"));
delete c.api_token;
process.stdout.write(JSON.stringify({
    ...c,
    mcp_port: Number(port),
    results_file: `${results}/harness.json`,
    versions: { client, server, "openid-client": oidc, jose },
}));
' "$CONFIG" "$results" "$STACK_HARNESS_MCP_PORT" \
  "$(version @modelcontextprotocol/client)" "$(version @modelcontextprotocol/server)" \
  "$(version openid-client)" "$(version jose)" |
  node harness/run.mjs 2>"$results/harness.stderr.log" || {
  echo "harness failed; see $results/harness.stderr.log" >&2
  exit 1
}

node -e '
const out = JSON.parse(require("node:fs").readFileSync(process.argv[1], "utf8"));
for (const [id, r] of Object.entries(out.results)) {
    console.log(`${r.status.padEnd(7)} ${id.padEnd(36)} ${r.summary}`.slice(0, 200));
}
' "$results/harness.json"
echo "== results: $results"
echo "   rerun:   tests/mcp_conformance_id_jag_mcp_client/stack/client.sh"
