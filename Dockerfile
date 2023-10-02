# Stage 1: Build website
FROM --platform=${BUILDPLATFORM} docker.io/node:20 as website-builder

ENV NODE_ENV=production

WORKDIR /work/website

RUN --mount=type=bind,target=/work/website/package.json,src=./website/package.json \
    --mount=type=bind,target=/work/website/package-lock.json,src=./website/package-lock.json \
    --mount=type=cache,target=/root/.npm \
    npm ci --include=dev

COPY ./website /work/website/
COPY ./blueprints /work/blueprints/
COPY ./SECURITY.md /work/

RUN npm run build-docs-only

# Stage 2: Build webui
FROM --platform=${BUILDPLATFORM} docker.io/node:20 as web-builder

ENV NODE_ENV=production

WORKDIR /work/web

RUN --mount=type=bind,target=/work/web/package.json,src=./web/package.json \
    --mount=type=bind,target=/work/web/package-lock.json,src=./web/package-lock.json \
    --mount=type=cache,target=/root/.npm \
    npm ci --include=dev

COPY ./web /work/web/
COPY ./website /work/website/
COPY ./gen-ts-api /work/web/node_modules/@goauthentik/api

RUN npm run build

# Stage 3: Build go proxy
FROM docker.io/golang:1.21.1-bookworm AS go-builder

WORKDIR /go/src/goauthentik.io

RUN --mount=type=bind,target=/go/src/goauthentik.io/go.mod,src=./go.mod \
    --mount=type=bind,target=/go/src/goauthentik.io/go.sum,src=./go.sum \
    --mount=type=cache,target=/go/pkg/mod \
    go mod download

COPY ./cmd /go/src/goauthentik.io/cmd
COPY ./authentik/lib /go/src/goauthentik.io/authentik/lib
COPY ./web/static.go /go/src/goauthentik.io/web/static.go
COPY --from=web-builder /work/web/robots.txt /go/src/goauthentik.io/web/robots.txt
COPY --from=web-builder /work/web/security.txt /go/src/goauthentik.io/web/security.txt
COPY ./internal /go/src/goauthentik.io/internal
COPY ./go.mod /go/src/goauthentik.io/go.mod
COPY ./go.sum /go/src/goauthentik.io/go.sum

ENV CGO_ENABLED=0

RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    go build -o /go/authentik ./cmd/server

# Stage 4: MaxMind GeoIP
FROM ghcr.io/maxmind/geoipupdate:v6.0 as geoip

ENV GEOIPUPDATE_EDITION_IDS="GeoLite2-City"
ENV GEOIPUPDATE_VERBOSE="true"
ENV GEOIPUPDATE_ACCOUNT_ID_FILE="/run/secrets/GEOIPUPDATE_ACCOUNT_ID"
ENV GEOIPUPDATE_LICENSE_KEY_FILE="/run/secrets/GEOIPUPDATE_LICENSE_KEY"

USER root
RUN --mount=type=secret,id=GEOIPUPDATE_ACCOUNT_ID \
    --mount=type=secret,id=GEOIPUPDATE_LICENSE_KEY \
    mkdir -p /usr/share/GeoIP && \
    /bin/sh -c "/usr/bin/entry.sh || echo 'Failed to get GeoIP database, disabling'; exit 0"

# Stage 5: Python dependencies
FROM docker.io/python:3.11.5-bookworm AS python-deps

WORKDIR /ak-root/poetry

ENV VENV_PATH="/ak-root/venv" \
    POETRY_VIRTUALENVS_CREATE=false \
    PATH="/ak-root/venv/bin:$PATH"

RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && \
    # Required for installing pip packages
    apt-get install -y --no-install-recommends build-essential pkg-config libxmlsec1-dev zlib1g-dev libpq-dev

RUN --mount=type=bind,target=./pyproject.toml,src=./pyproject.toml \
    --mount=type=bind,target=./poetry.lock,src=./poetry.lock \
    --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/root/.cache/pypoetry \
    python -m venv /ak-root/venv/ && \
    pip3 install --upgrade pip && \
    pip3 install poetry && \
    poetry install --only=main --no-ansi --no-interaction

# Stage 6: Run
FROM docker.io/python:3.11.5-slim-bookworm AS final-image

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
    apt-get install -y --no-install-recommends libpq5 openssl libxmlsec1-openssl libmaxminddb0 && \
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
COPY --from=website-builder /work/website/help/ /website/help/
COPY --from=geoip /usr/share/GeoIP /geoip

USER 1000

ENV TMPDIR=/dev/shm/ \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/ak-root/venv/bin:/lifecycle:$PATH" \
    VENV_PATH="/ak-root/venv" \
    POETRY_VIRTUALENVS_CREATE=false

HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 CMD [ "ak", "healthcheck" ]

ENTRYPOINT [ "dumb-init", "--", "ak" ]
