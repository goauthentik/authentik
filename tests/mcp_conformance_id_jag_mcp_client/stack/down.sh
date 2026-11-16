#!/usr/bin/env bash
# Stop the e2e stack: close its Rex session, remove the database container, and delete the
# stack's state (credentials and secret key). Results directories are kept.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
load_env

if [[ -n "${STACK_REX_SESSION:-}" ]]; then
  "$(rex_bin)" kill "$STACK_REX_SESSION" >/dev/null 2>&1 || true
fi
docker rm -f "$STACK_CONTAINER" >/dev/null 2>&1 || true
rm -rf "$STATE"
echo "== stack stopped"
