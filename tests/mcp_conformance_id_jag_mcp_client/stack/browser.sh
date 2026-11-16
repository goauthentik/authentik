#!/usr/bin/env bash
# Stack tab: the browser walkthrough (harness/browser.mjs). Open the printed URL, sign in to
# authentik, and the page runs the rest of the ID-JAG flow with the official MCP SDK against
# the long-running MCP server.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
load_env

wait_for "authentik to be configured" test -f "$CONFIG"
exec node "$SUITE/harness/browser.mjs" "$CONFIG" "$STACK_CALLBACK_PORT" "$STACK_MCP_PORT"
