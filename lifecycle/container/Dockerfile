# syntax=docker/dockerfile:1

# Tag must track the root package.json `packageManager` version. ${BUILDPLATFORM}
# keeps the binary's arch aligned with the builder stage on cross-arch builds.
FROM --platform=${BUILDPLATFORM} ghcr.io/pnpm/pnpm:12.4.0@sha256:4fcb6db39468ecafef34f3e866730df106f7639ba4512e42885d80f868ccb257 AS pnpm

# Stage: Build webui
FROM --platform=${BUILDPLATFORM} docker.io/library/node:26-trixie-slim@sha256:d82e1d091233ff0f771fc6c22837fa64c1019806ae2ac76cf5345cbc1e01668a AS node-builder

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
    node ./scripts/node/lint-runtime.ts ./web

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
FROM ghcr.io/goauthentik/fips-debian:trixie-slim-fips-pr-178@sha256:cd66513ddc1a2735f120db27add7dffa409f601fec3ec813a69bba9b126e845e AS rust-toolchain

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
FROM ghcr.io/astral-sh/uv:0.12.21@sha256:a7aed3216253ee804de3e2d8afa5073baa1a177335345d43845cd4165e43b711 AS uv
# Stage: Base python image
# TEMPORARY: pinned to goauthentik/fips#178 (remove wget/curl). Revert before merge.
FROM ghcr.io/goauthentik/fips-python:3.14.7-slim-trixie-fips-pr-178@sha256:395b057183f7e567f3cef6b06e7dffd5e10b7e8bedb94866b613449e1ca5ab28 AS python-base

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

# Stage: Test kit
# Test-only files that scripts/test_docker.sh mounts into the unchanged final or distroless image
# Build it with --target test-kit and an output, like scripts/test_docker.sh does

# MIT KDC tools for the Kerberos tests.
FROM python-base AS test-kit-kdc

RUN apt-get update && \
    apt-get install -y --no-install-recommends krb5-kdc krb5-admin-server krb5-user busybox-static

# Wrappers that run the tools from where the filesystem is mounted, /test-kit/krb5/root
RUN libdir="$(dirname "$(readlink -f /usr/lib/*/libkrb5.so.3)")" && \
    loader="$(readlink -f /lib*/ld-linux*.so.*)" && \
    mkdir -p /kit/bin /kit/plugins && \
    # k5test loads the database module from <plugins>/kdc
    ln -s "../root$libdir/krb5/plugins/kdb" /kit/plugins/kdc && \
    for tool in krb5kdc kadmind kdb5_util kadmin.local kadmin kprop kinit klist; do \
    # readlink resolves Debian's alternatives, whose absolute links would point into the image
    printf '#!/test-kit/krb5/root%s sh\nexec /test-kit/krb5/root%s --library-path /test-kit/krb5/root%s /test-kit/krb5/root%s "$@"\n' \
    "$(readlink -f "$(command -v busybox)")" "$loader" "$libdir" "$(readlink -f "$(command -v $tool)")" > /kit/bin/$tool; \
    done && \
    chmod 755 /kit/bin/*

FROM python-base AS test-kit-build

# The dev-only Python packages: the dev group minus every package the image ships
RUN --mount=type=bind,target=pyproject.toml,src=pyproject.toml \
    --mount=type=bind,target=uv.lock,src=uv.lock \
    uv export --frozen --no-hashes --no-emit-project --no-emit-workspace --no-header --no-annotate \
    --no-dev --output-file /tmp/shipped.txt && \
    uv export --frozen --no-hashes --no-emit-project --no-emit-workspace --no-header --no-annotate \
    --only-group dev --output-file /tmp/dev.txt && \
    # Compare names, the environment markers can differ between the two
    awk -F'[ =;]' 'NR == FNR { shipped[$1]; next } !($1 in shipped)' /tmp/shipped.txt /tmp/dev.txt > /tmp/dev-only.txt && \
    uv pip install --no-deps --target /kit/devdeps -r /tmp/dev-only.txt

COPY --from=test-kit-kdc / /kit/krb5/root/
COPY --from=test-kit-kdc /kit/ /kit/krb5/
COPY ./tests/container/sitecustomize.py /kit/sc/sitecustomize.py
COPY ./tests/container/check_dev_imports.py /kit/check_dev_imports.py

FROM scratch AS test-kit

COPY --from=test-kit-build /kit/ /

# Stage: assemble the runtime filesystem
# Shared by the distroless image and the final image
FROM python-base AS runtime-assemble

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
    libkadm5clnt-mit12 libkadm5clnt7t64-heimdal \
    libltdl7 libxslt1.1 && \
    apt-get purge -y curl libcurl4t64 && \
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
COPY --from=rust-builder /bin/authentik /bin/authentik
COPY ./packages/ /ak-root/packages
RUN ln -s /ak-root/packages /packages && \
    ln -s ak.py /lifecycle/ak
COPY --from=python-deps /ak-root/.venv /ak-root/.venv
COPY --from=node-builder /work/web/dist/ /web/dist/
COPY --from=node-builder /work/web/authentik/ /web/authentik/
COPY --from=geoip /usr/share/GeoIP /geoip

# Stage: distroless root filesystem
# prune.sh copies the files the distroless image needs into /out
FROM runtime-assemble AS distroless-rootfs

RUN --mount=type=bind,target=/tmp/prune.sh,src=./lifecycle/container/prune.sh \
    --mount=type=bind,target=/tmp/runtime-packages.txt,src=./lifecycle/container/runtime-packages.txt \
    --mount=type=bind,target=/tmp/runtime-paths.txt,src=./lifecycle/container/runtime-paths.txt \
    --mount=type=bind,target=/tmp/runtime-drop.txt,src=./lifecycle/container/runtime-drop.txt \
    bash /tmp/prune.sh /tmp/runtime-packages.txt /tmp/runtime-paths.txt /tmp/runtime-drop.txt

# Stage: Run, distroless
# Contains only what's needed at runtime and nothing more
# Build it with --target distroless as it is not the default
FROM scratch AS distroless

ARG VERSION
ARG GIT_BUILD_HASH
ENV GIT_BUILD_HASH=$GIT_BUILD_HASH

LABEL org.opencontainers.image.authors="Authentik Security Inc." \
    org.opencontainers.image.source="https://github.com/goauthentik/authentik" \
    org.opencontainers.image.description="goauthentik.io Main server image, see https://goauthentik.io for more info." \
    org.opencontainers.image.documentation="https://docs.goauthentik.io" \
    org.opencontainers.image.licenses="https://github.com/goauthentik/authentik/blob/main/LICENSE" \
    org.opencontainers.image.revision=${GIT_BUILD_HASH} \
    org.opencontainers.image.title="authentik server image (distroless)" \
    org.opencontainers.image.url="https://goauthentik.io" \
    org.opencontainers.image.vendor="Authentik Security Inc." \
    org.opencontainers.image.version=${VERSION}

# The copies are split so a rebuild does not invalidate unchanged layers
# /out-root holds the merged-usr symlinks (bin, lib, lib64, sbin) and the top level files, trailing slash required!
COPY --from=distroless-rootfs /out-root/ /
COPY --from=distroless-rootfs /out/usr /usr
COPY --from=distroless-rootfs /out/etc /etc
COPY --from=distroless-rootfs /out/var /var
COPY --from=distroless-rootfs /out/tmp /tmp
COPY --from=distroless-rootfs /out/run /run
COPY --from=distroless-rootfs /out/geoip /geoip
COPY --from=distroless-rootfs /out/ak-root /ak-root
COPY --from=distroless-rootfs /out/web /web
COPY --from=distroless-rootfs /out/locale /locale
COPY --from=distroless-rootfs /out/schemas /schemas
COPY --from=distroless-rootfs /out/blueprints /blueprints
COPY --from=distroless-rootfs /out/lifecycle /lifecycle
COPY --from=distroless-rootfs /out/authentik /authentik
COPY --chown=1000:1000 --from=distroless-rootfs /out/certs /certs
COPY --chown=1000:1000 --from=distroless-rootfs /out/data /data
COPY --chown=1000:1000 --from=distroless-rootfs /out/media /media

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

# Stage: Run
# The default target, so it has to stay last
FROM runtime-assemble AS final

USER 1000

ENV TMPDIR=/dev/shm/ \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    GOFIPS=1 \
    RUST_BACKTRACE=full

HEALTHCHECK --interval=30s --timeout=30s --start-period=120s --retries=3 CMD [ "ak", "healthcheck" ]

ENTRYPOINT [ "dumb-init", "--", "ak" ]
