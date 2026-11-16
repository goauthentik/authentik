# Shared by the stack scripts (sourced, not run). Paths, the stack's state directory, Node,
# and the stack's environment. Never loads local.env.yml or touches the developer database.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SUITE="$ROOT/tests/mcp_conformance_id_jag_mcp_client"
STATE="$SUITE/.stack"
ENV_FILE="$STATE/env"
CONFIG="$STATE/config.json"
SESSION_LABEL="id-jag-e2e"

# Prefer nvm's Node 24.22.2 when present; otherwise use the Node on PATH.
NVM_NODE="${NVM_DIR:-$HOME/.nvm}/versions/node/v24.22.2/bin"
if [[ -x "$NVM_NODE/node" ]]; then
  export PATH="$NVM_NODE:$PATH"
fi

rex_bin() {
  if [[ -n "${REX:-}" ]]; then
    echo "$REX"
  elif command -v rex >/dev/null 2>&1; then
    command -v rex
  else
    echo "/Applications/Rex Beta.app/Contents/Helpers/Rex Server.rex/Contents/MacOS/rex"
  fi
}

load_env() {
  if [[ ! -f "$ENV_FILE" ]]; then
    echo "no stack environment at $ENV_FILE: start the stack with stack/up.sh" >&2
    exit 1
  fi
  set -a
  # shellcheck source=/dev/null
  source "$ENV_FILE"
  set +a
}

# Wait until a command succeeds, printing a note once
wait_for() {
  local what="$1"
  shift
  local tries=0
  until "$@" >/dev/null 2>&1; do
    if ((tries == 0)); then echo "waiting for $what..."; fi
    tries=$((tries + 1))
    if ((tries > 600)); then
      echo "gave up waiting for $what" >&2
      return 1
    fi
    sleep 1
  done
}
