# Stage 1: Build website
FROM --platform=${BUILDPLATFORM} docker.io/node:20 as website-builder

COPY ./website /work/website/
COPY ./blueprints /work/blueprints/
COPY ./SECURITY.md /work/

ENV NODE_ENV=production
WORKDIR /work/website
RUN npm ci --include=dev && npm run build-docs-only

# Stage 2: Build webui
FROM --platform=${BUILDPLATFORM} docker.io/node:20 as web-builder

COPY ./web /work/web/
COPY ./website /work/website/

ENV NODE_ENV=production
WORKDIR /work/web
RUN npm ci --include=dev && npm run build

# Stage 3: Poetry to requirements.txt export
FROM docker.io/python:3.11.4-slim-bullseye AS poetry-locker

WORKDIR /work
COPY ./pyproject.toml /work
COPY ./poetry.lock /work

RUN pip install --no-cache-dir poetry && \
    poetry export -f requirements.txt --output requirements.txt && \
    poetry export -f requirements.txt --dev --output requirements-dev.txt

# Stage 4: Build go proxy
FROM docker.io/golang:1.20.5-bullseye AS go-builder

WORKDIR /work

COPY --from=web-builder /work/web/robots.txt /work/web/robots.txt
COPY --from=web-builder /work/web/security.txt /work/web/security.txt

COPY ./cmd /work/cmd
COPY ./web/static.go /work/web/static.go
COPY ./internal /work/internal
COPY ./go.mod /work/go.mod
COPY ./go.sum /work/go.sum

RUN go build -o /work/authentik ./cmd/server/

# Stage 5: MaxMind GeoIP
FROM ghcr.io/maxmind/geoipupdate:v5.1 as geoip

ENV GEOIPUPDATE_EDITION_IDS="GeoLite2-City"
ENV GEOIPUPDATE_VERBOSE="true"

USER root
RUN --mount=type=secret,id=GEOIPUPDATE_ACCOUNT_ID \
    --mount=type=secret,id=GEOIPUPDATE_LICENSE_KEY \
    mkdir -p /usr/share/GeoIP && \
    /bin/sh -c "\
        export GEOIPUPDATE_ACCOUNT_ID=$(cat /run/secrets/GEOIPUPDATE_ACCOUNT_ID); \
        export GEOIPUPDATE_LICENSE_KEY=$(cat /run/secrets/GEOIPUPDATE_LICENSE_KEY); \
        /usr/bin/entry.sh || echo 'Failed to get GeoIP database, disabling'; exit 0 \
    "

# Stage 6: Run
FROM docker.io/python:3.11.4-slim-bullseye AS final-image

LABEL org.opencontainers.image.url https://goauthentik.io
LABEL org.opencontainers.image.description goauthentik.io Main server image, see https://goauthentik.io for more info.
LABEL org.opencontainers.image.source https://github.com/goauthentik/authentik

WORKDIR /

ARG GIT_BUILD_HASH
ENV GIT_BUILD_HASH=$GIT_BUILD_HASH

COPY --from=poetry-locker /work/requirements.txt /
COPY --from=poetry-locker /work/requirements-dev.txt /
COPY --from=geoip /usr/share/GeoIP /geoip

RUN apt-get update && \
    # Required for installing pip packages
    apt-get install -y --no-install-recommends build-essential pkg-config libxmlsec1-dev zlib1g-dev && \
    # Required for runtime
    apt-get install -y --no-install-recommends libxmlsec1-openssl libmaxminddb0 && \
    # Required for bootstrap & healtcheck
    apt-get install -y --no-install-recommends runit && \
    pip install --no-cache-dir -r /requirements.txt && \
    apt-get remove --purge -y build-essential pkg-config libxmlsec1-dev && \
    apt-get autoremove --purge -y && \
    apt-get clean && \
    rm -rf /tmp/* /var/lib/apt/lists/* /var/tmp/ && \
    adduser --system --no-create-home --uid 1000 --group --home /authentik authentik && \
    mkdir -p /certs /media /blueprints && \
    mkdir -p /authentik/.ssh && \
    chown authentik:authentik /certs /media /authentik/.ssh

COPY ./authentik/ /authentik
COPY ./pyproject.toml /
COPY ./schemas /schemas
COPY ./locale /locale
COPY ./tests /tests
COPY ./manage.py /
COPY ./blueprints /blueprints
COPY ./lifecycle/ /lifecycle
COPY --from=go-builder /work/authentik /bin/authentik
COPY --from=web-builder /work/web/dist/ /web/dist/
COPY --from=web-builder /work/web/authentik/ /web/authentik/
COPY --from=website-builder /work/website/help/ /website/help/

USER 1000

ENV TMPDIR /dev/shm/
ENV PYTHONUNBUFFERED 1
ENV PATH "/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/lifecycle"

HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 CMD [ "/lifecycle/ak", "healthcheck" ]

ENTRYPOINT [ "/usr/local/bin/dumb-init", "--", "/lifecycle/ak" ]
