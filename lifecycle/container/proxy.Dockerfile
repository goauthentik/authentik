# syntax=docker/dockerfile:1

<<<<<<< HEAD
# Stage 1: Build web
FROM --platform=${BUILDPLATFORM} docker.io/library/node:24 AS web-builder
=======
# Stage: Build
FROM ghcr.io/goauthentik/fips-debian:trixie-slim-fips@sha256:b97a9f4f34c7d1ea350e394bb0cd14f2f5bfc39517bc442534bf6005ff2bc084 AS builder
>>>>>>> 8b2496a4b (core: bump goauthentik/fips-debian from 7726387 to b97a9f4 in /lifecycle/container (#27306))

ENV NODE_ENV=production
WORKDIR /static

# These files need to be copied and cannot be mounted as `npm ci` will build the client's typescript
COPY ./packages /packages
COPY ./web/packages /static/packages

COPY package.json /
RUN --mount=type=bind,target=/static/package.json,src=./web/package.json \
    --mount=type=bind,target=/static/package-lock.json,src=./web/package-lock.json \
    --mount=type=bind,target=/static/scripts,src=./web/scripts \
    --mount=type=cache,target=/root/.npm \
    npm ci

COPY web .
RUN npm run build-proxy

# Stage 2: Build
FROM --platform=${BUILDPLATFORM} docker.io/library/golang:1.26.5-trixie@sha256:4ee9ffa999b4583ce281939cdff828763083610292f252279a0cee77473bd9a7 AS builder

ARG TARGETOS
ARG TARGETARCH
ARG TARGETVARIANT

ARG GOOS=$TARGETOS
ARG GOARCH=$TARGETARCH

WORKDIR /go/src/goauthentik.io

RUN --mount=type=cache,id=apt-$TARGETARCH$TARGETVARIANT,sharing=locked,target=/var/cache/apt \
    dpkg --add-architecture arm64 && \
    apt-get update && \
<<<<<<< HEAD
    apt-get install -y --no-install-recommends crossbuild-essential-arm64 gcc-aarch64-linux-gnu
=======
    # Required for installing pip packages
    apt-get install -y --no-install-recommends \
    # Build essentials
    build-essential \
    curl \
    # aws-lc deps
    cmake clang golang && \
    curl https://sh.rustup.rs -sSf | sh -s -- -y --profile minimal --default-toolchain none && \
    rustup install && \
    rustup default "$(sed -n 's/channel = "\(.*\)"/\1/p' rust-toolchain.toml)" && \
    rustc --version && \
    cargo --version
# See https://github.com/aws/aws-lc-rs/issues/569
ENV AWS_LC_FIPS_SYS_CC=clang
>>>>>>> 8b2496a4b (core: bump goauthentik/fips-debian from 7726387 to b97a9f4 in /lifecycle/container (#27306))

RUN --mount=type=bind,target=/go/src/goauthentik.io/go.mod,src=./go.mod \
    --mount=type=bind,target=/go/src/goauthentik.io/go.sum,src=./go.sum \
    --mount=type=cache,target=/go/pkg/mod \
    go mod download

<<<<<<< HEAD
COPY . .
RUN --mount=type=cache,sharing=locked,target=/go/pkg/mod \
    --mount=type=cache,id=go-build-$TARGETARCH$TARGETVARIANT,sharing=locked,target=/root/.cache/go-build \
    if [ "$TARGETARCH" = "arm64" ]; then export CC=aarch64-linux-gnu-gcc && export CC_FOR_TARGET=gcc-aarch64-linux-gnu; fi && \
    CGO_ENABLED=1 GOFIPS140=latest GOARM="${TARGETVARIANT#v}" \
    go build -o /go/proxy ./cmd/proxy

# Stage 3: Run
FROM ghcr.io/goauthentik/fips-debian:trixie-slim-fips@sha256:7726387c78b5787d2146868c2ccc8948a3591d0a5a6436f7780c8c28acc76341
=======
# Stage: Run
FROM ghcr.io/goauthentik/fips-debian:trixie-slim-fips@sha256:b97a9f4f34c7d1ea350e394bb0cd14f2f5bfc39517bc442534bf6005ff2bc084
>>>>>>> 8b2496a4b (core: bump goauthentik/fips-debian from 7726387 to b97a9f4 in /lifecycle/container (#27306))

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

COPY --from=builder /go/proxy /
COPY --from=web-builder /static/robots.txt /web/robots.txt
COPY --from=web-builder /static/security.txt /web/security.txt
COPY --from=web-builder /static/dist/ /web/dist/
COPY --from=web-builder /static/authentik/ /web/authentik/

HEALTHCHECK --interval=5s --retries=20 --start-period=3s CMD [ "/proxy", "healthcheck" ]

EXPOSE 9000 9300 9443

USER 1000

ENV TMPDIR=/dev/shm/ \
    GOFIPS=1

ENTRYPOINT ["/proxy"]
