#!/usr/bin/env bash
# Print shell exports for poking at the running stack from any terminal:
#   eval "$(tests/mcp_conformance_id_jag_mcp_client/stack/env.sh)"
# AK, MCP and DEMO are base URLs; C is the stack's config.json (credentials, mode 0600); H is
# the latest client run's harness.json. Database settings and the secret key aren't exported.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
load_env

latest="$(ls -d "$SUITE"/results/*-stack 2>/dev/null | tail -n1 || true)"
cat <<EOF
export STACK_AK_PORT=$STACK_AK_PORT STACK_MCP_PORT=$STACK_MCP_PORT STACK_CALLBACK_PORT=$STACK_CALLBACK_PORT
export AK=http://localhost:$STACK_AK_PORT MCP=http://localhost:$STACK_MCP_PORT DEMO=http://localhost:$STACK_CALLBACK_PORT
export C=$CONFIG
export H=${latest:+$latest/harness.json}
EOF
