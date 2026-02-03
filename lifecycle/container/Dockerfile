# syntax=docker/dockerfile:1

# Stage 1: Build webui
FROM --platform=${BUILDPLATFORM} docker.io/library/node:24-trixie-slim@sha256:45babd1b4ce0349fb12c4e24bf017b90b96d52806db32e001e3013f341bef0fe AS node-builder

ARG GIT_BUILD_HASH
ENV GIT_BUILD_HASH=$GIT_BUILD_HASH
ENV NODE_ENV=production

WORKDIR /work/web

RUN --mount=type=bind,target=/work/web/package.json,src=./web/package.json \
    --mount=type=bind,target=/work/web/package-lock.json,src=./web/package-lock.json \
    --mount=type=bind,target=/work/web/packages/sfe/package.json,src=./web/packages/sfe/package.json \
    --mount=type=bind,target=/work/web/scripts,src=./web/scripts \
    --mount=type=cache,id=npm-ak,sharing=shared,target=/root/.npm \
    npm ci

COPY ./package.json /work
COPY ./web /work/web/
# TODO: Update this after moving website to docs
COPY ./website /work/website/
COPY ./gen-ts-api /work/web/node_modules/@goauthentik/api

RUN npm run build && \
    npm run build:sfe

# Stage 2: Build go proxy
FROM --platform=${BUILDPLATFORM} docker.io/library/golang:1.25.5-trixie@sha256:8e8f9c84609b6005af0a4a8227cee53d6226aab1c6dcb22daf5aeeb8b05480e1 AS go-builder

ARG TARGETOS
ARG TARGETARCH
ARG TARGETVARIANT

ARG GOOS=$TARGETOS
ARG GOARCH=$TARGETARCH

WORKDIR /go/src/goauthentik.io

RUN --mount=type=cache,id=apt-$TARGETARCH$TARGETVARIANT,sharing=locked,target=/var/cache/apt \
    dpkg --add-architecture arm64 && \
    apt-get update && \
    apt-get install -y --no-install-recommends crossbuild-essential-arm64 gcc-aarch64-linux-gnu

RUN --mount=type=bind,target=/go/src/goauthentik.io/go.mod,src=./go.mod \
    --mount=type=bind,target=/go/src/goauthentik.io/go.sum,src=./go.sum \
    --mount=type=bind,target=/go/src/goauthentik.io/gen-go-api,src=./gen-go-api \
    --mount=type=cache,target=/go/pkg/mod \
    go mod download

COPY ./cmd /go/src/goauthentik.io/cmd
COPY ./authentik/lib /go/src/goauthentik.io/authentik/lib
COPY ./web/static.go /go/src/goauthentik.io/web/static.go
COPY --from=node-builder /work/web/robots.txt /go/src/goauthentik.io/web/robots.txt
COPY --from=node-builder /work/web/security.txt /go/src/goauthentik.io/web/security.txt
COPY ./internal /go/src/goauthentik.io/internal
COPY ./go.mod /go/src/goauthentik.io/go.mod
COPY ./go.sum /go/src/goauthentik.io/go.sum

RUN --mount=type=cache,sharing=locked,target=/go/pkg/mod \
    --mount=type=bind,target=/go/src/goauthentik.io/gen-go-api,src=./gen-go-api \
    --mount=type=cache,id=go-build-$TARGETARCH$TARGETVARIANT,sharing=locked,target=/root/.cache/go-build \
    if [ "$TARGETARCH" = "arm64" ]; then export CC=aarch64-linux-gnu-gcc && export CC_FOR_TARGET=gcc-aarch64-linux-gnu; fi && \
    CGO_ENABLED=1 GOFIPS140=latest GOARM="${TARGETVARIANT#v}" \
    go build -o /go/authentik ./cmd/server

# Stage 3: MaxMind GeoIP
FROM --platform=${BUILDPLATFORM} ghcr.io/maxmind/geoipupdate:v7.1.1@sha256:faecdca22579730ab0b7dea5aa9af350bb3c93cb9d39845c173639ead30346d2 AS geoip

ENV GEOIPUPDATE_EDITION_IDS="GeoLite2-City GeoLite2-ASN"
ENV GEOIPUPDATE_VERBOSE="1"
ENV GEOIPUPDATE_ACCOUNT_ID_FILE="/run/secrets/GEOIPUPDATE_ACCOUNT_ID"

USER root
RUN --mount=type=secret,id=GEOIPUPDATE_ACCOUNT_ID \
    --mount=type=secret,id=GEOIPUPDATE_LICENSE_KEY \
    mkdir -p /usr/share/GeoIP && \
    /bin/sh -c "GEOIPUPDATE_LICENSE_KEY_FILE=/run/secrets/GEOIPUPDATE_LICENSE_KEY /usr/bin/entry.sh || echo 'Failed to get GeoIP database, disabling'; exit 0"

# Stage 4: Download uv
FROM ghcr.io/astral-sh/uv:0.9.18@sha256:5713fa8217f92b80223bc83aac7db36ec80a84437dbc0d04bbc659cae030d8c9 AS uv
# Stage 5: Base python image
FROM ghcr.io/goauthentik/fips-python:3.14.2-slim-trixie-fips@sha256:46c0658052e43ad303da39e461ad106c499a03fabd3512d05ff586e506507242 AS python-base

ENV VENV_PATH="/ak-root/.venv" \
    PATH="/lifecycle:/ak-root/.venv/bin:$PATH" \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NATIVE_TLS=1 \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /ak-root/

COPY --from=uv /uv /uvx /bin/

# Stage 6: Python dependencies
FROM python-base AS python-deps

ARG TARGETARCH
ARG TARGETVARIANT

RUN rm -f /etc/apt/apt.conf.d/docker-clean; echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache

ENV PATH="/root/.cargo/bin:$PATH"

RUN --mount=type=cache,id=apt-$TARGETARCH$TARGETVARIANT,sharing=locked,target=/var/cache/apt \
    apt-get update && \
    # Required for installing pip packages
    apt-get install -y --no-install-recommends \
    # Build essentials
    build-essential pkg-config libffi-dev git \
    # cryptography
    curl \
    # libxml
    libxslt-dev zlib1g-dev \
    # postgresql
    libpq-dev \
    # python-kadmin-rs
    krb5-multidev libkrb5-dev heimdal-multidev libclang-dev \
    # xmlsec
    libltdl-dev && \
    curl https://sh.rustup.rs -sSf | sh -s -- -y

ENV UV_NO_BINARY_PACKAGE="cryptography lxml python-kadmin-rs xmlsec" \
    # https://github.com/rust-lang/rustup/issues/2949
    # Fixes issues where the rust version in the build cache is older than latest
    # and rustup tries to update it, which fails
    RUSTUP_PERMIT_COPY_RENAME="true"

RUN --mount=type=bind,target=pyproject.toml,src=pyproject.toml \
    --mount=type=bind,target=uv.lock,src=uv.lock \
    --mount=type=bind,target=packages,src=packages \
    --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Stage 7: Run
FROM python-base AS final-image

ARG VERSION
ARG GIT_BUILD_HASH
ENV GIT_BUILD_HASH=$GIT_BUILD_HASH

LABEL org.opencontainers.image.authors="Authentik Security Inc." \
    org.opencontainers.image.source="https://github.com/goauthentik/authentik" \
    org.opencontainers.image.description="goauthentik.io Main server image, see https://goauthentik.io for more info." \
    org.opencontainers.image.documentation="https://docs.goauthentik.io" \
    org.opencontainers.image.licenses="https://github.com/goauthentik/authentik/blob/main/LICENSE" \
    org.opencontainers.image.revision=${GIT_BUILD_HASH} \
    org.opencontainers.image.source="https://github.com/goauthentik/authentik" \
    org.opencontainers.image.title="authentik server image" \
    org.opencontainers.image.url="https://goauthentik.io" \
    org.opencontainers.image.vendor="Authentik Security Inc." \
    org.opencontainers.image.version=${VERSION}

WORKDIR /

# We cannot cache this layer otherwise we'll end up with a bigger image
RUN apt-get update && \
    apt-get upgrade -y && \
    # Required for runtime
    apt-get install -y --no-install-recommends \
    libpq5 libmaxminddb0 ca-certificates \
    krb5-multidev libkrb5-3 libkdb5-10 libkadm5clnt-mit12 \
    heimdal-multidev libkadm5clnt7t64-heimdal \
    libltdl7 libxslt1.1 && \
    # Required for bootstrap & healtcheck
    apt-get install -y --no-install-recommends runit && \
    pip3 install --no-cache-dir --upgrade pip && \
    apt-get clean && \
    rm -rf /tmp/* /var/lib/apt/lists/* /var/tmp/ && \
    adduser --system --no-create-home --uid 1000 --group --home /authentik authentik && \
    mkdir -p /certs /data /media /blueprints && \
    ln -s /media /data/media && \
    mkdir -p /authentik/.ssh && \
    mkdir -p /ak-root && \
    chown authentik:authentik /certs /data /data/media /media /authentik/.ssh /ak-root

COPY ./authentik/ /authentik
COPY ./pyproject.toml /
COPY ./uv.lock /
COPY ./schemas /schemas
COPY ./locale /locale
COPY ./tests /tests
COPY ./manage.py /
COPY ./blueprints /blueprints
COPY ./lifecycle/ /lifecycle
COPY ./authentik/sources/kerberos/krb5.conf /etc/krb5.conf
COPY --from=go-builder /go/authentik /bin/authentik
COPY ./packages/ /ak-root/packages
RUN  ln -s /ak-root/packages /packages
COPY --from=python-deps /ak-root/.venv /ak-root/.venv
COPY --from=node-builder /work/web/dist/ /web/dist/
COPY --from=node-builder /work/web/authentik/ /web/authentik/
COPY --from=geoip /usr/share/GeoIP /geoip

USER 1000

ENV TMPDIR=/dev/shm/ \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    GOFIPS=1

HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 CMD [ "ak", "healthcheck" ]

ENTRYPOINT [ "dumb-init", "--", "ak" ]
