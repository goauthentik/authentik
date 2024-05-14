# syntax=docker/dockerfile:1

# Stage 1: Build
FROM --platform=${BUILDPLATFORM} mcr.microsoft.com/oss/go/microsoft/golang:1.22-fips-bookworm AS builder

ARG TARGETOS
ARG TARGETARCH
ARG TARGETVARIANT

ARG GOOS=$TARGETOS
ARG GOARCH=$TARGETARCH

WORKDIR /go/src/goauthentik.io

RUN --mount=type=bind,target=/go/src/goauthentik.io/go.mod,src=./go.mod \
    --mount=type=bind,target=/go/src/goauthentik.io/go.sum,src=./go.sum \
    --mount=type=bind,target=/go/src/goauthentik.io/gen-go-api,src=./gen-go-api \
    --mount=type=cache,target=/go/pkg/mod \
    go mod download

COPY . .
RUN --mount=type=cache,sharing=locked,target=/go/pkg/mod \
    --mount=type=cache,id=go-build-$TARGETARCH$TARGETVARIANT,sharing=locked,target=/root/.cache/go-build \
    CGO_ENABLED=1 GOEXPERIMENT="systemcrypto" GOFLAGS="-tags=requirefips" GOARM="${TARGETVARIANT#v}" go build -o /go/ldap ./cmd/ldap

# Stage 2: Run
FROM ghcr.io/goauthentik/fips-debian:bookworm-slim-fips

ARG GIT_BUILD_HASH
ENV GIT_BUILD_HASH=$GIT_BUILD_HASH

LABEL org.opencontainers.image.url https://goauthentik.io
LABEL org.opencontainers.image.description goauthentik.io LDAP outpost, see https://goauthentik.io for more info.
LABEL org.opencontainers.image.source https://github.com/goauthentik/authentik
LABEL org.opencontainers.image.version ${VERSION}
LABEL org.opencontainers.image.revision ${GIT_BUILD_HASH}

COPY --from=builder /go/ldap /

HEALTHCHECK --interval=5s --retries=20 --start-period=3s CMD [ "/ldap", "healthcheck" ]

EXPOSE 3389 6636 9300

USER 1000

ENV GOFIPS=1

ENTRYPOINT ["/ldap"]
