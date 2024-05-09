# syntax=docker/dockerfile:1

# Stage 1: Build website
FROM --platform=${BUILDPLATFORM} docker.io/node:22 as website-builder

ENV NODE_ENV=production

WORKDIR /work/website

RUN --mount=type=bind,target=/work/website/package.json,src=./website/package.json \
    --mount=type=bind,target=/work/website/package-lock.json,src=./website/package-lock.json \
    --mount=type=cache,id=npm-website,sharing=shared,target=/root/.npm \
    npm ci --include=dev

COPY ./website /work/website/
COPY ./blueprints /work/blueprints/
COPY ./schema.yml /work/
COPY ./SECURITY.md /work/

RUN npm run build-bundled

# Stage 2: Generate static Typescript files
FROM --platform=${BUILDPLATFORM} docker.io/python:3.12.0-slim-bookworm AS npm-version

RUN --mount=type=bind,target=./scripts/npm_version.py,src=./scripts/npm_version.py \
    --mount=type=bind,target=./authentik,src=./authentik \
    python -m scripts.npm_version > /NPM_VERSION

FROM --platform=${BUILDPLATFORM} docker.io/openapitools/openapi-generator-cli:v6.5.0 as ts-generator

WORKDIR /local

COPY ./schema.yml .
COPY ./scripts/api-ts-config.yaml ./scripts/api-ts-config.yaml
COPY ./scripts/api-ts-templates ./scripts/api-ts-templates
COPY --from=npm-version /NPM_VERSION .

RUN NPM_VERSION=$(cat ./NPM_VERSION) && \
    /usr/local/bin/docker-entrypoint.sh generate \
    -i /local/schema.yml -g typescript-fetch -o /local/gen-ts-api -c /local/scripts/api-ts-config.yaml \
    --additional-properties=npmVersion=${NPM_VERSION} --git-repo-id authentik --git-user-id goauthentik

# Stage 3: Build webui
FROM --platform=${BUILDPLATFORM} docker.io/node:22 as web-builder

ENV NODE_ENV=production

WORKDIR /work/web

RUN --mount=type=bind,target=/work/web/package.json,src=./web/package.json \
    --mount=type=bind,target=/work/web/package-lock.json,src=./web/package-lock.json \
    --mount=type=cache,id=npm-web,sharing=shared,target=/root/.npm \
    npm ci --include=dev

COPY ./web /work/web/
COPY ./website /work/website/
COPY --from=ts-generator /local/gen-ts-api /work/web/node_modules/@goauthentik/api

RUN cd /work/web/node_modules/@goauthentik/api && \
    npm install

RUN npm run build

# Stage 4: Generate static Go files
FROM --platform=${BUILDPLATFORM} docker.io/openapitools/openapi-generator-cli:v6.5.0 as go-generator

WORKDIR /local

RUN mkdir -p templates && \
    wget https://raw.githubusercontent.com/goauthentik/client-go/main/config.yaml -O ./config.yaml && \
	wget https://raw.githubusercontent.com/goauthentik/client-go/main/templates/README.mustache -O ./templates/README.mustache && \
	wget https://raw.githubusercontent.com/goauthentik/client-go/main/templates/go.mod.mustache -O ./templates/go.mod.mustache

COPY ./schema.yml .

RUN /usr/local/bin/docker-entrypoint.sh generate \
    -i /local/schema.yml -g go -o /local/ -c /local/config.yaml && \
    rm -rf /local/config.yaml /local/templates

# Stage 5: Build go proxy
FROM --platform=${BUILDPLATFORM} docker.io/golang:1.22.3-bookworm AS go-builder

ARG TARGETOS
ARG TARGETARCH
ARG TARGETVARIANT

ARG GOOS=$TARGETOS
ARG GOARCH=$TARGETARCH

WORKDIR /go/src/goauthentik.io

COPY --from=go-generator /local /go/src/goauthentik.io/gen-go-api

COPY ./go.mod /go/src/goauthentik.io/go.mod
COPY ./go.sum /go/src/goauthentik.io/go.sum

RUN --mount=type=cache,target=/go/pkg/mod \
    go mod edit -replace goauthentik.io/api/v3=./gen-go-api && \
    go mod download

COPY ./cmd /go/src/goauthentik.io/cmd
COPY ./authentik/lib /go/src/goauthentik.io/authentik/lib
COPY ./web/static.go /go/src/goauthentik.io/web/static.go
COPY --from=web-builder /work/web/robots.txt /go/src/goauthentik.io/web/robots.txt
COPY --from=web-builder /work/web/security.txt /go/src/goauthentik.io/web/security.txt
COPY ./internal /go/src/goauthentik.io/internal

ENV CGO_ENABLED=0

RUN --mount=type=cache,sharing=locked,target=/go/pkg/mod \
    --mount=type=cache,id=go-build-$TARGETARCH$TARGETVARIANT,sharing=locked,target=/root/.cache/go-build \
    GOARM="${TARGETVARIANT#v}" go build -o /go/authentik ./cmd/server

# Stage 6: MaxMind GeoIP
FROM --platform=${BUILDPLATFORM} ghcr.io/maxmind/geoipupdate:v7.0.1 as geoip

ENV GEOIPUPDATE_EDITION_IDS="GeoLite2-City GeoLite2-ASN"
ENV GEOIPUPDATE_VERBOSE="1"
ENV GEOIPUPDATE_ACCOUNT_ID_FILE="/run/secrets/GEOIPUPDATE_ACCOUNT_ID"
ENV GEOIPUPDATE_LICENSE_KEY_FILE="/run/secrets/GEOIPUPDATE_LICENSE_KEY"

USER root
RUN --mount=type=secret,id=GEOIPUPDATE_ACCOUNT_ID \
    --mount=type=secret,id=GEOIPUPDATE_LICENSE_KEY \
    mkdir -p /usr/share/GeoIP && \
    /bin/sh -c "/usr/bin/entry.sh || echo 'Failed to get GeoIP database, disabling'; exit 0"

# Stage 7: Python dependencies
FROM docker.io/python:3.12.3-slim-bookworm AS python-deps

WORKDIR /ak-root/poetry

ENV VENV_PATH="/ak-root/venv" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    PATH="/ak-root/venv/bin:$PATH"

RUN rm -f /etc/apt/apt.conf.d/docker-clean; echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache

RUN --mount=type=cache,id=apt-$TARGETARCH$TARGETVARIANT,sharing=locked,target=/var/cache/apt \
    apt-get update && \
    # Required for installing pip packages
    apt-get install -y --no-install-recommends build-essential pkg-config libxmlsec1-dev zlib1g-dev libpq-dev

RUN --mount=type=bind,target=./pyproject.toml,src=./pyproject.toml \
    --mount=type=bind,target=./poetry.lock,src=./poetry.lock \
    --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/root/.cache/pypoetry \
    python -m venv /ak-root/venv/ && \
    bash -c "source ${VENV_PATH}/bin/activate && \
        pip3 install --upgrade pip && \
        pip3 install poetry && \
        poetry install --only=main --no-ansi --no-interaction --no-root"

# Stage 8: Run
FROM docker.io/python:3.12.3-slim-bookworm AS final-image

ARG GIT_BUILD_HASH
ARG VERSION
ENV GIT_BUILD_HASH=$GIT_BUILD_HASH

LABEL org.opencontainers.image.url https://goauthentik.io
LABEL org.opencontainers.image.description goauthentik.io Main server image, see https://goauthentik.io for more info.
LABEL org.opencontainers.image.source https://github.com/goauthentik/authentik
LABEL org.opencontainers.image.version ${VERSION}
LABEL org.opencontainers.image.revision ${GIT_BUILD_HASH}

WORKDIR /

# We cannot cache this layer otherwise we'll end up with a bigger image
RUN apt-get update && \
    # Required for runtime
    apt-get install -y --no-install-recommends libpq5 openssl libxmlsec1-openssl libmaxminddb0 ca-certificates && \
    # Required for bootstrap & healtcheck
    apt-get install -y --no-install-recommends runit && \
    apt-get clean && \
    rm -rf /tmp/* /var/lib/apt/lists/* /var/tmp/ && \
    adduser --system --no-create-home --uid 1000 --group --home /authentik authentik && \
    mkdir -p /certs /media /blueprints && \
    mkdir -p /authentik/.ssh && \
    mkdir -p /ak-root && \
    chown authentik:authentik /certs /media /authentik/.ssh /ak-root

COPY ./authentik/ /authentik
COPY ./pyproject.toml /
COPY ./poetry.lock /
COPY ./schemas /schemas
COPY ./locale /locale
COPY ./tests /tests
COPY ./manage.py /
COPY ./blueprints /blueprints
COPY ./lifecycle/ /lifecycle
COPY --from=go-builder /go/authentik /bin/authentik
COPY --from=python-deps /ak-root/venv /ak-root/venv
COPY --from=web-builder /work/web/dist/ /web/dist/
COPY --from=web-builder /work/web/authentik/ /web/authentik/
COPY --from=website-builder /work/website/build/ /website/help/
COPY --from=geoip /usr/share/GeoIP /geoip

USER 1000

ENV TMPDIR=/dev/shm/ \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/ak-root/venv/bin:/lifecycle:$PATH" \
    VENV_PATH="/ak-root/venv" \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 CMD [ "ak", "healthcheck" ]

ENTRYPOINT [ "dumb-init", "--", "ak" ]
