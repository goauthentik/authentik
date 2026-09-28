#!/usr/bin/env bash
# Test the server image without changing it, test-only files are mounted.
set -e -x -o pipefail
hash="$(git rev-parse HEAD || openssl rand -base64 36 | sha256sum)"

AUTHENTIK_IMAGE="${AUTHENTIK_IMAGE:-authentik.invalid/goauthentik/server}"
AUTHENTIK_TAG="${AUTHENTIK_TAG:-$(echo "$hash" | cut -c1-15)}"

if [ -f lifecycle/container/.env ]; then
    echo "Existing .env file, aborting"
    exit 1
fi

echo PG_PASS="$(openssl rand -base64 36 | tr -d '\n')" >lifecycle/container/.env
echo AUTHENTIK_SECRET_KEY="$(openssl rand -base64 60 | tr -d '\n')" >>lifecycle/container/.env
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-authentik-test-${AUTHENTIK_TAG}}"
export COMPOSE_FILE=lifecycle/container/compose.yml

if [[ -v BUILD ]]; then
    echo AUTHENTIK_IMAGE="${AUTHENTIK_IMAGE}" >>lifecycle/container/.env
    echo AUTHENTIK_TAG="${AUTHENTIK_TAG}" >>lifecycle/container/.env

    # Ensure buildx is installed
    docker buildx install
    touch lifecycle/container/.env

    docker build -t "${AUTHENTIK_IMAGE}:${AUTHENTIK_TAG}" -f lifecycle/container/Dockerfile .
fi

kit="$(mktemp -d)"
# mktemp creates it 0700, but the image reads it as uid 1000
chmod 755 "$kit"
# A tar stream, as the local exporter can hang, https://github.com/moby/buildkit/issues/4453
docker buildx build --target test-kit --output type=tar,dest=- -f lifecycle/container/Dockerfile . |
    tar -x -C "$kit"

# Check that shipped code doesn't import a package only the test kit provides, because it would
# pass the tests and fail in production. All shards would find the same, so the first one checks
if [ "${CI_RUN_ID:-1}" = 1 ]; then
    docker compose run --rm --no-deps -v "${kit}:/test-kit:ro" \
        --entrypoint /ak-root/.venv/bin/python server /test-kit/check_dev_imports.py
fi

docker compose run --rm \
    -v "${kit}:/test-kit:ro" \
    -v "${PWD}/tests:/tests:ro" \
    -e PYTEST_ADDOPTS=--junitxml=/dev/shm/unittest.xml \
    -e PYTHONPATH=/test-kit/sc \
    -e CI -e CI_RUN_ID -e CI_TOTAL_RUNS -e CI_TEST_SEED -e GITHUB_ACTIONS \
    server test-all
docker compose down -v
