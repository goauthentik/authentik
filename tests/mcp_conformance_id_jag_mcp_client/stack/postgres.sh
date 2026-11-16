#!/usr/bin/env bash
# Stack pane: a disposable PostgreSQL container in the foreground, on a loopback port. The
# container is removed when this pane's process exits (Ctrl-C) or stack/down.sh runs.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
load_env

exec docker run --rm --name "$STACK_CONTAINER" \
  -e POSTGRES_USER="$AUTHENTIK_POSTGRESQL__USER" \
  -e POSTGRES_PASSWORD="$AUTHENTIK_POSTGRESQL__PASSWORD" \
  -e POSTGRES_DB="$AUTHENTIK_POSTGRESQL__NAME" \
  -p "127.0.0.1:$AUTHENTIK_POSTGRESQL__PORT:5432" docker.io/library/postgres:16
