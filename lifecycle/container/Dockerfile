# syntax=docker/dockerfile:1

# Stage 1: Build webui
FROM --platform=${BUILDPLATFORM} docker.io/library/node:24-trixie-slim@sha256:735dd688da64d22ebd9dd374b3e7e5a874635668fd2a6ec20ca1f99264294086 AS node-builder

ARG GIT_BUILD_HASH
ENV GIT_BUILD_HASH=$GIT_BUILD_HASH
ENV NODE_ENV=production

WORKDIR /work/web

# These files need to be copied and cannot be mounted as `npm ci` will build the client's typescript
COPY ./packages /work/packages
COPY ./web/packages /work/web/packages

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

RUN npm run build && \
    npm run build:sfe

# Stage 2: Build go proxy
FROM --platform=${BUILDPLATFORM} docker.io/library/golang:1.26.2-trixie@sha256:982ae929f9a74083a242c6e25d19d7d9ed78c6e97fab639a119e90707ba819e2 AS go-builder

ARG TARGETOS
ARG TARGETARCH
ARG TARGETVARIANT

ARG GOOS=$TARGETOS
ARG GOARCH=$TARGETARCH

WORKDIR /go/src/goauthentik.io

RUN --mount=type=cache,id=apt-$TARGETARCH$TARGETVARIANT,sharing=locked,target=/var/cache/apt \
    dpkg --add-architecture arm64 && \
    dpkg --add-architecture amd64 && \
    apt-get update && \
    apt-get install -y --no-install-recommends crossbuild-essential-arm64 gcc-aarch64-linux-gnu crossbuild-essential-amd64 gcc-x86-64-linux-gnu

RUN --mount=type=bind,target=/go/src/goauthentik.io/go.mod,src=./go.mod \
    --mount=type=bind,target=/go/src/goauthentik.io/go.sum,src=./go.sum \
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
COPY ./packages/client-go /go/src/goauthentik.io/packages/client-go

RUN --mount=type=cache,sharing=locked,target=/go/pkg/mod \
    --mount=type=cache,id=go-build-$TARGETARCH$TARGETVARIANT,sharing=locked,target=/root/.cache/go-build \
    if [ "$TARGETARCH" = "arm64" ] && [ "$(uname -m)" != "aarch64" ]; then export CC=aarch64-linux-gnu-gcc && export CC_FOR_TARGET=gcc-aarch64-linux-gnu; fi && \
    if [ "$TARGETARCH" = "amd64" ] && [ "$(uname -m)" != "x86_64" ]; then export CC=x86_64-linux-gnu-gcc; fi && \
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
FROM ghcr.io/astral-sh/uv:0.11.5@sha256:555ac94f9a22e656fc5f2ce5dfee13b04e94d099e46bb8dd3a73ec7263f2e484 AS uv
# Stage 5: Base python image
FROM ghcr.io/goauthentik/fips-python:3.14.3-slim-trixie-fips@sha256:bf45eb77a010d76fe6abd7ae137d1b0c44b6227cd984945042135fdf05ebf8d9 AS python-base

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
    --mount=type=bind,target=rust-toolchain.toml,src=rust-toolchain.toml \
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
    export RUST_TOOLCHAIN="$(awk -F'\"' '/^[[:space:]]*channel[[:space:]]*=/{print $2; exit}' rust-toolchain.toml)" && \
    curl https://sh.rustup.rs -sSf | sh -s -- -y --profile minimal --default-toolchain "${RUST_TOOLCHAIN}" && \
    rustup default "${RUST_TOOLCHAIN}" && \
    rustc --version && \
    cargo --version

ENV UV_NO_BINARY_PACKAGE="cryptography lxml python-kadmin-rs xmlsec" \
    # https://github.com/rust-lang/rustup/issues/2949
    # Fixes issues where the rust version in the build cache is older than latest
    # and rustup tries to update it, which fails
    RUSTUP_PERMIT_COPY_RENAME="1"

RUN --mount=type=bind,target=pyproject.toml,src=pyproject.toml \
    --mount=type=bind,target=uv.lock,src=uv.lock \
    --mount=type=bind,target=packages,src=packages \
    --mount=type=bind,target=rust-toolchain.toml,src=rust-toolchain.toml \
    --mount=type=cache,id=uv-python-deps-$TARGETARCH$TARGETVARIANT,target=/root/.cache/uv \
    RUSTUP_TOOLCHAIN="$(awk -F'\"' '/^[[:space:]]*channel[[:space:]]*=/{print $2; exit}' rust-toolchain.toml)" \
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
