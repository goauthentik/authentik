#!/usr/bin/env bash
set -e -x -o pipefail
hash="$(git rev-parse HEAD || openssl rand -base64 36 | sha256sum)"

AUTHENTIK_IMAGE="xghcr.io/goauthentik/server"
AUTHENTIK_TAG="$(echo "$hash" | cut -c1-15)"

if [ -f lifecycle/container/.env ]; then
    echo "Existing .env file, aborting"
    exit 1
fi

echo PG_PASS="$(openssl rand -base64 36 | tr -d '\n')" >lifecycle/container/.env
echo AUTHENTIK_SECRET_KEY="$(openssl rand -base64 60 | tr -d '\n')" >>lifecycle/container/.env
export COMPOSE_PROJECT_NAME="authentik-test-${AUTHENTIK_TAG}"

if [[ -v BUILD ]]; then
    echo AUTHENTIK_IMAGE="${AUTHENTIK_IMAGE}" >>lifecycle/container/.env
    echo AUTHENTIK_TAG="${AUTHENTIK_TAG}" >>lifecycle/container/.env

    # Ensure buildx is installed
    docker buildx install
    # For release builds we have an empty client here as we use the NPM package
    mkdir -p ./gen-ts-api
    touch lifecycle/container/.env

    docker build -t "${AUTHENTIK_IMAGE}:${AUTHENTIK_TAG}" .
fi

docker compose -f lifecycle/container/docker-compose.yml up --no-start
docker compose -f lifecycle/container/docker-compose.yml start postgresql redis
docker compose -f lifecycle/container/docker-compose.yml run -u root server test-all
docker compose -f lifecycle/container/docker-compose.yml down -v
