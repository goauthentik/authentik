#!/bin/bash
set -e -x -o pipefail
hash=$(git rev-parse HEAD || openssl rand -base64 36)

export PG_PASS=$(openssl rand -base64 36 | tr -d '\n')
export AUTHENTIK_SECRET_KEY=$(openssl rand -base64 60 | tr -d '\n')
export AUTHENTIK_IMAGE="xghcr.io/goauthentik/server"
export AUTHENTIK_TAG=$(echo $hash | cut -c1-15)
export COMPOSE_PROJECT_NAME="authentik-test-${AUTHENTIK_TAG}"

# Ensure buildx is installed
docker buildx install
# For release builds we have an empty client here as we use the NPM package
mkdir -p ./gen-ts-api
touch .env

docker build -t ${AUTHENTIK_IMAGE}:${AUTHENTIK_TAG} .
docker compose up --no-start
docker compose start postgresql redis
docker compose run -u root server test-all
docker compose down -v
