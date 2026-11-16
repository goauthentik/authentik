#!/usr/bin/env bash
# Stack pane: the MCP server fixture (official server SDK) as a long-running Protected
# Resource whose metadata names authentik's Resource AS provider. Logs every request it
# authorizes or refuses.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
load_env

wait_for "authentik to be configured" test -f "$CONFIG"
exec node "$SUITE/harness/serve.mjs" "$CONFIG" "$STACK_MCP_PORT"
