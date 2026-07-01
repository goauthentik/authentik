# syntax=docker/dockerfile:1

# Stage 1: Build web
FROM --platform=${BUILDPLATFORM} docker.io/library/node:26 AS web-builder

ENV NODE_ENV=production
WORKDIR /static

# These files need to be copied and cannot be mounted as `npm ci` will build the client's typescript
COPY ./packages /packages
COPY ./web/packages /static/packages

RUN --mount=type=bind,target=/static/package.json,src=./package.json \
    --mount=type=bind,target=/static/package-lock.json,src=./package-lock.json \
    --mount=type=bind,target=/static/web/package.json,src=./web/package.json \
    --mount=type=bind,target=/static/web/package-lock.json,src=./web/package-lock.json \
    --mount=type=bind,target=/static/scripts/node/,src=./scripts/node/ \
    --mount=type=bind,target=/static/packages/logger-js/,src=./packages/logger-js/ \
    node ./scripts/node/setup-corepack.mjs --force && \
    node ./scripts/node/lint-runtime.mjs ./web

COPY package.json /

RUN --mount=type=bind,target=/static/.npmrc,src=./.npmrc \
    --mount=type=bind,target=/static/package.json,src=./web/package.json \
    --mount=type=bind,target=/static/package-lock.json,src=./web/package-lock.json \
    --mount=type=bind,target=/static/scripts,src=./web/scripts \
    --mount=type=cache,target=/root/.npm \
    corepack npm ci

COPY web .
RUN npm run build-proxy

# Stage 2: Build
FROM ghcr.io/goauthentik/fips-debian:trixie-slim-fips@sha256:7726387c78b5787d2146868c2ccc8948a3591d0a5a6436f7780c8c28acc76341 AS builder

ARG TARGETARCH
ARG TARGETVARIANT

ENV PATH="/root/.cargo/bin:$PATH"
SHELL ["/bin/sh", "-o", "pipefail", "-c"]
RUN rm -f /etc/apt/apt.conf.d/docker-clean; echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache
RUN --mount=type=cache,id=apt-$TARGETARCH$TARGETVARIANT,sharing=locked,target=/var/cache/apt \
    --mount=type=bind,target=rust-toolchain.toml,src=rust-toolchain.toml \
    apt-get update && \
    # Required for installing pip packages
    apt-get install -y --no-install-recommends \
    # Build essentials
    build-essential \
    # aws-lc deps
    cmake clang golang && \
    curl https://sh.rustup.rs -sSf | sh -s -- -y --profile minimal --default-toolchain none && \
    rustup install && \
    rustup default "$(sed -n 's/channel = "\(.*\)"/\1/p' rust-toolchain.toml)" && \
    rustc --version && \
    cargo --version
# See https://github.com/aws/aws-lc-rs/issues/569
ENV AWS_LC_FIPS_SYS_CC=clang

RUN --mount=type=bind,target=rust-toolchain.toml,src=rust-toolchain.toml \
    --mount=type=bind,target=Cargo.toml,src=Cargo.toml \
    --mount=type=bind,target=Cargo.lock,src=Cargo.lock \
    --mount=type=bind,target=.cargo/,src=.cargo/ \
    --mount=type=bind,target=src/,src=src/ \
    --mount=type=bind,target=packages/,src=packages/ \
    --mount=type=bind,target=authentik/lib/default.yml,src=authentik/lib/default.yml \
    # Required otherwise workspace discovery fails
    --mount=type=bind,target=website/scripts/docsmg/,src=website/scripts/docsmg/ \
    --mount=type=cache,id=cargo-git-db-$TARGETARCH$TARGETVARIANT,target=/root/.cargo/git/db/ \
    --mount=type=cache,id=cargo-registry-$TARGETARCH$TARGETVARIANT,target=/root/.cargo/registry/ \
    --mount=type=cache,id=rust-target-$TARGETARCH$TARGETVARIANT,target=/build/target/ \
    cargo build --package authentik --no-default-features --features proxy --locked --release && \
    cp ./target/release/authentik /bin/authentik

# Stage 3: Run
FROM ghcr.io/goauthentik/fips-debian:trixie-slim-fips@sha256:7726387c78b5787d2146868c2ccc8948a3591d0a5a6436f7780c8c28acc76341

ARG VERSION
ARG GIT_BUILD_HASH
ENV GIT_BUILD_HASH=$GIT_BUILD_HASH

LABEL org.opencontainers.image.authors="Authentik Security Inc." \
    org.opencontainers.image.source="https://github.com/goauthentik/authentik" \
    org.opencontainers.image.description="goauthentik.io Proxy outpost image, see https://goauthentik.io for more info." \
    org.opencontainers.image.documentation="https://docs.goauthentik.io" \
    org.opencontainers.image.licenses="https://github.com/goauthentik/authentik/blob/main/LICENSE" \
    org.opencontainers.image.revision=${GIT_BUILD_HASH} \
    org.opencontainers.image.title="authentik proxy outpost image" \
    org.opencontainers.image.url="https://goauthentik.io" \
    org.opencontainers.image.vendor="Authentik Security Inc." \
    org.opencontainers.image.version=${VERSION}

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get clean && \
    rm -rf /tmp/* /var/lib/apt/lists/*

COPY --from=builder /bin/authentik /
COPY --from=web-builder /static/robots.txt /web/robots.txt
COPY --from=web-builder /static/security.txt /web/security.txt
COPY --from=web-builder /static/dist/ /web/dist/
COPY --from=web-builder /static/authentik/ /web/authentik/

HEALTHCHECK --interval=5s --retries=20 --start-period=3s CMD [ "/authentik", "healthcheck", "proxy" ]

EXPOSE 9000 9300 9443

USER 1000

ENV TMPDIR=/dev/shm/ \
    RUST_BACKTRACE=full

ENTRYPOINT ["/authentik", "proxy"]
