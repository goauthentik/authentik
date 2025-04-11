# syntax=docker/dockerfile:1

# Stage 1: Build web
FROM --platform=${BUILDPLATFORM} docker.io/library/node:22 AS web-builder

ENV NODE_ENV=production
WORKDIR /static

COPY ./package.json ./package.json
COPY ./package-lock.json ./package-lock.json
COPY ./packages ./packages
COPY ./web ./web

RUN --mount=type=cache,target=/root/.npm npm ci --include=dev
RUN npm run build-proxy -w @goauthentik/web


# Stage 2: Build
FROM --platform=${BUILDPLATFORM} docker.io/library/golang:1.24-bookworm AS builder

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

COPY . .
RUN --mount=type=cache,sharing=locked,target=/go/pkg/mod \
    --mount=type=cache,id=go-build-$TARGETARCH$TARGETVARIANT,sharing=locked,target=/root/.cache/go-build \
    if [ "$TARGETARCH" = "arm64" ]; then export CC=aarch64-linux-gnu-gcc && export CC_FOR_TARGET=gcc-aarch64-linux-gnu; fi && \
    CGO_ENABLED=1 GOFIPS140=latest GOARM="${TARGETVARIANT#v}" \
    go build -o /go/proxy ./cmd/proxy

# Stage 3: Run
FROM ghcr.io/goauthentik/fips-debian:bookworm-slim-fips

ARG VERSION
ARG GIT_BUILD_HASH
ENV GIT_BUILD_HASH=$GIT_BUILD_HASH

LABEL org.opencontainers.image.url=https://goauthentik.io
LABEL org.opencontainers.image.description="goauthentik.io Proxy outpost image, see https://goauthentik.io for more info."
LABEL org.opencontainers.image.source=https://github.com/goauthentik/authentik
LABEL org.opencontainers.image.version=${VERSION}
LABEL org.opencontainers.image.revision=${GIT_BUILD_HASH}

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get clean && \
    rm -rf /tmp/* /var/lib/apt/lists/*

COPY --from=builder /go/proxy /
COPY --from=web-builder /static/web/robots.txt /web/robots.txt
COPY --from=web-builder /static/web/security.txt /web/security.txt
COPY --from=web-builder /static/web/dist/ /web/dist/
COPY --from=web-builder /static/web/authentik/ /web/authentik/

HEALTHCHECK --interval=5s --retries=20 --start-period=3s CMD [ "/proxy", "healthcheck" ]

EXPOSE 9000 9300 9443

USER 1000

ENV GOFIPS=1

ENTRYPOINT ["/proxy"]
