# Stage 1: Build website
FROM --platform=${BUILDPLATFORM} docker.io/node:20.5 as website-builder

ENV NODE_ENV=production

WORKDIR /work/website

COPY ./website/package.json /work/website/package.json
COPY ./website/package-lock.json /work/website/package-lock.json

RUN --mount=type=cache,target=/root/.npm \
    npm ci --include=dev

COPY ./website /work/website/
COPY ./blueprints /work/blueprints/
COPY ./SECURITY.md /work/

RUN npm run build-docs-only

# Stage 2: Build webui
FROM --platform=${BUILDPLATFORM} docker.io/node:20.5 as web-builder

ENV NODE_ENV=production

WORKDIR /work/web

COPY ./web/package.json /work/web/package.json
COPY ./web/package-lock.json /work/web/package-lock.json

RUN --mount=type=cache,target=/root/.npm \
    npm ci --include=dev

COPY ./web /work/web/
COPY ./website /work/website/

RUN npm run build

# Stage 3: Build go proxy
FROM docker.io/golang:1.21.1-bookworm AS go-builder

WORKDIR /work

COPY --from=web-builder /work/web/robots.txt /work/web/robots.txt
COPY --from=web-builder /work/web/security.txt /work/web/security.txt

COPY ./cmd /work/cmd
COPY ./authentik/lib /work/authentik/lib
COPY ./web/static.go /work/web/static.go
COPY ./internal /work/internal
COPY ./go.mod /work/go.mod
COPY ./go.sum /work/go.sum

RUN go build -o /work/bin/authentik ./cmd/server/

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

WORKDIR /work

ENV VENV_PATH="/work/venv" \
    PATH="/work/venv/bin:$PATH"

RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && \
    # Required for installing pip packages
    apt-get install -y --no-install-recommends build-essential pkg-config libxmlsec1-dev zlib1g-dev libpq-dev

RUN --mount=type=bind,target=./pyproject.toml,src=./pyproject.toml \
    --mount=type=bind,target=./poetry.lock,src=./poetry.lock \
    --mount=type=cache,target=/root/.cache/pypoetry \
    python -m venv /work/venv/ && \
    pip3 install --upgrade pip && \
    pip3 install poetry && \
    poetry install --only=main

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

COPY --from=geoip /usr/share/GeoIP /geoip

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
    chown authentik:authentik /certs /media /authentik/.ssh

COPY ./authentik/ /authentik
COPY ./pyproject.toml /
COPY ./poetry.lock /
COPY ./schemas /schemas
COPY ./locale /locale
COPY ./tests /tests
COPY ./manage.py /
COPY ./blueprints /blueprints
COPY ./lifecycle/ /lifecycle
COPY --from=go-builder /work/bin/authentik /bin/authentik
COPY --from=python-deps /work/venv /venv
COPY --from=web-builder /work/web/dist/ /web/dist/
COPY --from=web-builder /work/web/authentik/ /web/authentik/
COPY --from=website-builder /work/website/help/ /website/help/

USER 1000

ENV TMPDIR=/dev/shm/ \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/venv/bin:$PATH"

HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 CMD [ "/lifecycle/ak", "healthcheck" ]

ENTRYPOINT [ "/usr/local/bin/dumb-init", "--", "/lifecycle/ak" ]
