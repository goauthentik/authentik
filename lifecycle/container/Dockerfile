# syntax=docker/dockerfile:1

# Tag must track the root package.json `packageManager` version. ${BUILDPLATFORM}
# keeps the binary's arch aligned with the builder stage on cross-arch builds.
FROM --platform=${BUILDPLATFORM} ghcr.io/pnpm/pnpm:11.20.0@sha256:d77573aba1649491010d3d252214be47197c0706417793cf393ac47cc324f315 AS pnpm

# Stage: Build webui
FROM --platform=${BUILDPLATFORM} docker.io/library/node:26-trixie-slim@sha256:715e55e4b84e4bb0ff48e49b398a848f08e55daed8eb6a0ea1839ae53bc57583 AS node-builder

ARG GIT_BUILD_HASH
ENV GIT_BUILD_HASH=$GIT_BUILD_HASH
ENV NODE_ENV=production

WORKDIR /work

COPY --from=pnpm /opt/pnpm /opt/pnpm
ENV PATH="/opt/pnpm:${PATH}"

RUN --mount=type=bind,target=/work/package.json,src=./package.json \
    --mount=type=bind,target=/work/web/package.json,src=./web/package.json \
    --mount=type=bind,target=/work/web/pnpm-lock.yaml,src=./web/pnpm-lock.yaml \
    --mount=type=bind,target=/work/scripts/node/,src=./scripts/node/ \
    --mount=type=bind,target=/work/packages/logger-js/,src=./packages/logger-js/ \
    node ./scripts/node/lint-runtime.mjs ./web

WORKDIR /work/web

# These files need to be copied and cannot be mounted as `pnpm install` will build the client's typescript
COPY ./packages /work/packages
COPY ./web/packages /work/web/packages

RUN --mount=type=bind,target=/work/.npmrc,src=./.npmrc \
    --mount=type=bind,target=/work/web/package.json,src=./web/package.json \
    --mount=type=bind,target=/work/web/pnpm-lock.yaml,src=./web/pnpm-lock.yaml \
    --mount=type=bind,target=/work/web/pnpm-workspace.yaml,src=./web/pnpm-workspace.yaml \
    --mount=type=bind,target=/work/web/packages/sfe/package.json,src=./web/packages/sfe/package.json \
    --mount=type=bind,target=/work/web/scripts,src=./web/scripts \
    --mount=type=cache,id=pnpm-ak,sharing=shared,target=/root/.local/share/pnpm/store \
    pnpm install --frozen-lockfile

COPY ./package.json /work
COPY ./web /work/web/
# TODO: Update this after moving website to docs
COPY ./website /work/website/

RUN pnpm run build && \
    pnpm run build:sfe

# Stage: MaxMind GeoIP
FROM --platform=${BUILDPLATFORM} ghcr.io/maxmind/geoipupdate:v8.0.0@sha256:51e70dd6f16cd3e4d845ac02d09940b10772a75b9d741427d235a78570923c1d AS geoip

ENV GEOIPUPDATE_EDITION_IDS="GeoLite2-City GeoLite2-ASN"
ENV GEOIPUPDATE_VERBOSE="1"
ENV GEOIPUPDATE_ACCOUNT_ID_FILE="/run/secrets/GEOIPUPDATE_ACCOUNT_ID"

USER root
RUN --mount=type=secret,id=GEOIPUPDATE_ACCOUNT_ID \
    --mount=type=secret,id=GEOIPUPDATE_LICENSE_KEY \
    mkdir -p /usr/share/GeoIP && \
    /bin/sh -c "GEOIPUPDATE_LICENSE_KEY_FILE=/run/secrets/GEOIPUPDATE_LICENSE_KEY /usr/bin/entry.sh || echo 'Failed to get GeoIP database, disabling'; exit 0"

# Stage: download Rust toolchain
# TEMPORARY: pinned to goauthentik/fips#178 (remove wget/curl). Revert before merge.
FROM ghcr.io/goauthentik/fips-debian:trixie-slim-fips-pr-178@sha256:e048842e22989f2c0eaa7029d8a3d662a816504b0a9275917b5832a02e8cecda AS rust-toolchain

ARG TARGETARCH
ARG TARGETVARIANT

ENV PATH="/root/.cargo/bin:$PATH"
SHELL ["/bin/sh", "-o", "pipefail", "-c"]
RUN --mount=type=bind,target=rust-toolchain.toml,src=rust-toolchain.toml \
    apt-get update && \
    # Required for installing pip packages
    apt-get install -y --no-install-recommends \
    # Build essentials
    build-essential \
    curl ca-certificates && \
    curl https://sh.rustup.rs -sSf | sh -s -- -y --profile minimal --default-toolchain none && \
    rustup install && \
    rustup default "$(sed -n 's/channel = "\(.*\)"/\1/p' rust-toolchain.toml)" && \
    rustc --version && \
    cargo --version

# Stage: Download uv
FROM ghcr.io/astral-sh/uv:0.11.32@sha256:df4cae8f3a96d175e2e5f992e597550000edbe78fdc2594d5cd8de1a217f504c AS uv
# Stage: Base python image
# TEMPORARY: pinned to goauthentik/fips#178 (remove wget/curl). Revert before merge.
FROM ghcr.io/goauthentik/fips-python:3.14.7-slim-trixie-fips-pr-178@sha256:9f7cb71b77da3d38b3c7b77bb1cd913e9db90270137321771e97d25b9d07e8e8 AS python-base

ENV VENV_PATH="/ak-root/.venv" \
    PATH="/lifecycle:/ak-root/.venv/bin:$PATH" \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NATIVE_TLS=1 \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /ak-root/

COPY --from=uv /uv /uvx /bin/

# Stage: build rust binary
FROM python-base AS rust-builder

ARG TARGETARCH
ARG TARGETVARIANT

WORKDIR /build

ENV PATH="/root/.cargo/bin:$PATH"
COPY --from=rust-toolchain /root/.rustup /root/.rustup
COPY --from=rust-toolchain /root/.cargo /root/.cargo

RUN rm -f /etc/apt/apt.conf.d/docker-clean; echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache
RUN --mount=type=cache,id=apt-$TARGETARCH$TARGETVARIANT,sharing=locked,target=/var/cache/apt \
    --mount=type=bind,target=rust-toolchain.toml,src=rust-toolchain.toml \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    # common dependencies
    build-essential \
    # aws-lc deps
    cmake clang golang
# See https://github.com/aws/aws-lc-rs/issues/569
ENV AWS_LC_FIPS_SYS_CC=clang

COPY --from=node-builder /work/web/robots.txt /build/web/robots.txt
COPY --from=node-builder /work/web/security.txt /build/web/security.txt
COPY --from=node-builder /work/web/dist/standalone/loading/startup.html /build/web/dist/standalone/loading/startup.html

RUN --mount=type=bind,target=rust-toolchain.toml,src=rust-toolchain.toml \
    --mount=type=bind,target=Cargo.toml,src=Cargo.toml \
    --mount=type=bind,target=Cargo.lock,src=Cargo.lock \
    --mount=type=bind,target=.cargo/,src=.cargo/ \
    --mount=type=bind,target=build.rs,src=build.rs \
    --mount=type=bind,target=src/,src=src/ \
    --mount=type=bind,target=packages/ak-axum,src=packages/ak-axum \
    --mount=type=bind,target=packages/ak-common,src=packages/ak-common \
    --mount=type=bind,target=packages/client-rust,src=packages/client-rust \
    --mount=type=bind,target=authentik/lib/default.yml,src=authentik/lib/default.yml \
    # Required otherwise workspace discovery fails
    --mount=type=bind,target=website/scripts/docsmg/,src=website/scripts/docsmg/ \
    --mount=type=cache,id=cargo-git-db-$TARGETARCH$TARGETVARIANT,target=/root/.cargo/git/db/ \
    --mount=type=cache,id=cargo-registry-$TARGETARCH$TARGETVARIANT,target=/root/.cargo/registry/ \
    --mount=type=cache,id=rust-target-$TARGETARCH$TARGETVARIANT,target=/build/target/ \
    cargo build --package authentik --no-default-features --features core --locked --release && \
    cp ./target/release/authentik /bin/authentik


# Stage: Python dependencies
FROM python-base AS python-deps

ARG TARGETARCH
ARG TARGETVARIANT

RUN rm -f /etc/apt/apt.conf.d/docker-clean; echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache
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
    libltdl-dev

ENV PATH="/root/.cargo/bin:$PATH"
COPY --from=rust-toolchain /root/.rustup /root/.rustup
COPY --from=rust-toolchain /root/.cargo /root/.cargo

ENV UV_NO_BINARY_PACKAGE="cryptography lxml python-kadmin-rs xmlsec"
RUN --mount=type=bind,target=pyproject.toml,src=pyproject.toml \
    --mount=type=bind,target=uv.lock,src=uv.lock \
    --mount=type=bind,target=packages/ak-guardian,src=packages/ak-guardian \
    --mount=type=bind,target=packages/django-channels-postgres,src=packages/django-channels-postgres \
    --mount=type=bind,target=packages/django-dramatiq-postgres,src=packages/django-dramatiq-postgres \
    --mount=type=bind,target=packages/django-postgres-cache,src=packages/django-postgres-cache \
    --mount=type=bind,target=rust-toolchain.toml,src=rust-toolchain.toml \
    --mount=type=cache,id=uv-python-deps-$TARGETARCH$TARGETVARIANT,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-dev

# Stage: assemble the runtime filesystem
# prune.sh copies the used files into /out, and the final stage starts FROM scratch
FROM python-base AS runtime-assemble

WORKDIR /

# Not cached on purpose: apt-get upgrade on every build is what keeps the OS packages current
RUN --mount=type=bind,target=/tmp/runtime-packages.txt,src=./lifecycle/container/runtime-packages.txt \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    $(sed -e 's/#.*//' -e '/^[[:space:]]*$/d' /tmp/runtime-packages.txt) && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    adduser --system --no-create-home --uid 1000 --group --home /authentik authentik && \
    mkdir -p /certs /data /media /blueprints /authentik/.ssh /ak-root && \
    ln -s /media /data/media && \
    chown authentik:authentik /certs /data /data/media /media /authentik/.ssh /ak-root

COPY ./authentik/ /authentik
COPY ./pyproject.toml /
COPY ./uv.lock /
COPY ./schemas /schemas
COPY ./locale /locale
COPY ./manage.py /
COPY ./blueprints /blueprints
COPY ./lifecycle/ /lifecycle
COPY ./authentik/sources/kerberos/krb5.conf /etc/krb5.conf
COPY --from=rust-builder /bin/authentik /bin/authentik
COPY ./packages/ /ak-root/packages
COPY --from=python-deps /ak-root/.venv /ak-root/.venv
COPY --from=node-builder /work/web/dist/ /web/dist/
COPY --from=node-builder /work/web/authentik/ /web/authentik/
COPY --from=geoip /usr/share/GeoIP /geoip

# Setup 'ak'
RUN ln -s /ak-root/packages /packages && \
    ln -sf /bin/authentik /lifecycle/ak

# Prune everything that is not needed
RUN --mount=type=bind,target=/tmp/prune.sh,src=./lifecycle/container/prune.sh \
    --mount=type=bind,target=/tmp/runtime-packages.txt,src=./lifecycle/container/runtime-packages.txt \
    --mount=type=bind,target=/tmp/runtime-paths.txt,src=./lifecycle/container/runtime-paths.txt \
    --mount=type=bind,target=/tmp/runtime-drop.txt,src=./lifecycle/container/runtime-drop.txt \
    bash /tmp/prune.sh /tmp/runtime-packages.txt /tmp/runtime-paths.txt /tmp/runtime-drop.txt

# Stage: Debug
# For `ak test-all`, AUTHENTIK_DEBUGGER and `docker exec ... bash`
# Build it with --target debug-image as it is not the default
FROM runtime-assemble AS debug-image

ARG VERSION
ARG GIT_BUILD_HASH
ENV GIT_BUILD_HASH=$GIT_BUILD_HASH

LABEL org.opencontainers.image.title="authentik server image (debug)" \
    org.opencontainers.image.version=${VERSION}

COPY ./tests /tests
# runtime-assemble already copied pyproject.toml and uv.lock to /, so uv syncs
# from there. Dropping --no-dev is what adds the dev dependency group that
# `ak test-all` needs. UV_NO_BINARY_PACKAGE matches the python-deps stage so
# that anything uv does rebuild is still built from source against the FIPS
# OpenSSL, rather than replaced with a prebuilt wheel.
ENV UV_NO_BINARY_PACKAGE="cryptography lxml python-kadmin-rs xmlsec"
RUN rm -rf /out /out-root && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    bash-completion curl git less procps vim-tiny \
    krb5-user krb5-kdc krb5-admin-server libkrb5-dev gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    UV_PROJECT_ENVIRONMENT=/ak-root/.venv uv sync --locked --no-install-project && \
    touch /unittest.xml && \
    chown authentik:authentik /unittest.xml

USER 1000
ENV TMPDIR=/dev/shm/ \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    GOFIPS=1 \
    RUST_BACKTRACE=full
HEALTHCHECK --interval=30s --timeout=30s --start-period=120s --retries=3 CMD [ "ak", "healthcheck" ]
ENTRYPOINT [ "dumb-init", "--", "ak" ]

# Stage: Run
# Contains only what's needed at runtime and nothing more
FROM scratch AS final-image

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

# The copies are split so a rebuild does not invalidate unchanged layers
# /out-root holds the merged-usr symlinks (bin, lib, lib64, sbin) and the top level files, trailing slash required!
COPY --from=runtime-assemble /out-root/ /
COPY --from=runtime-assemble /out/usr /usr
COPY --from=runtime-assemble /out/etc /etc
COPY --from=runtime-assemble /out/var /var
COPY --from=runtime-assemble /out/tmp /tmp
COPY --from=runtime-assemble /out/run /run
COPY --from=runtime-assemble /out/geoip /geoip
COPY --from=runtime-assemble /out/ak-root /ak-root
COPY --from=runtime-assemble /out/web /web
COPY --from=runtime-assemble /out/locale /locale
COPY --from=runtime-assemble /out/schemas /schemas
COPY --from=runtime-assemble /out/blueprints /blueprints
COPY --from=runtime-assemble /out/lifecycle /lifecycle
COPY --from=runtime-assemble /out/authentik /authentik
COPY --chown=1000:1000 --from=runtime-assemble /out/certs /certs
COPY --chown=1000:1000 --from=runtime-assemble /out/data /data
COPY --chown=1000:1000 --from=runtime-assemble /out/media /media

WORKDIR /
USER 1000

ENV PATH="/lifecycle:/ak-root/.venv/bin:/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin" \
    VENV_PATH="/ak-root/.venv" \
    TMPDIR=/dev/shm/ \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    GOFIPS=1 \
    RUST_BACKTRACE=full

HEALTHCHECK --interval=30s --timeout=30s --start-period=120s --retries=3 CMD [ "ak", "healthcheck" ]

ENTRYPOINT [ "dumb-init", "--", "ak" ]
