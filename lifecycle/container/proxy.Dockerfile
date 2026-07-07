# syntax=docker/dockerfile:1

# Tag must track the root package.json `packageManager` version. ${BUILDPLATFORM}
# keeps the binary's arch aligned with the builder stage on cross-arch builds.
FROM --platform=${BUILDPLATFORM} ghcr.io/pnpm/pnpm:11.10.0@sha256:9a6eb06d5f861d830fe27d85a91415e60527fa45ec45b52ee43c92a8aaf3bf8a AS pnpm

# Stage 1: Build web
FROM --platform=${BUILDPLATFORM} docker.io/library/node:26 AS web-builder

ENV NODE_ENV=production
WORKDIR /static

# These files need to be copied and cannot be mounted as `pnpm install` will build the client's typescript
COPY ./packages /packages
COPY ./web/packages /static/packages

COPY --from=pnpm /opt/pnpm /opt/pnpm
ENV PATH="/opt/pnpm:${PATH}"

RUN --mount=type=bind,target=/static/package.json,src=./package.json \
    --mount=type=bind,target=/static/web/package.json,src=./web/package.json \
    --mount=type=bind,target=/static/web/pnpm-lock.yaml,src=./web/pnpm-lock.yaml \
    --mount=type=bind,target=/static/scripts/node/,src=./scripts/node/ \
    --mount=type=bind,target=/static/packages/logger-js/,src=./packages/logger-js/ \
    node ./scripts/node/lint-runtime.mjs ./web

COPY package.json /

RUN --mount=type=bind,target=/static/.npmrc,src=./.npmrc \
    --mount=type=bind,target=/static/package.json,src=./web/package.json \
    --mount=type=bind,target=/static/pnpm-lock.yaml,src=./web/pnpm-lock.yaml \
    --mount=type=bind,target=/static/pnpm-workspace.yaml,src=./web/pnpm-workspace.yaml \
    --mount=type=bind,target=/static/scripts,src=./web/scripts \
    --mount=type=cache,target=/root/.local/share/pnpm/store \
    pnpm install --frozen-lockfile

COPY web .
RUN pnpm run build-proxy

# Stage 2: Build
FROM --platform=${BUILDPLATFORM} docker.io/library/golang:1.26.4-trixie@sha256:68b7145ec43d1820b9a56704554b53d1520aa2a15cb5233e374188a31b2a1bce AS builder

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
    --mount=type=cache,target=/go/pkg/mod \
    go mod download

COPY . .
RUN --mount=type=cache,sharing=locked,target=/go/pkg/mod \
    --mount=type=cache,id=go-build-$TARGETARCH$TARGETVARIANT,sharing=locked,target=/root/.cache/go-build \
    if [ "$TARGETARCH" = "arm64" ]; then export CC=aarch64-linux-gnu-gcc && export CC_FOR_TARGET=gcc-aarch64-linux-gnu; fi && \
    CGO_ENABLED=1 GOFIPS140=latest GOARM="${TARGETVARIANT#v}" \
    go build -o /go/proxy ./cmd/proxy

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
