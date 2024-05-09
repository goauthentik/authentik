# syntax=docker/dockerfile:1

# Stage 1: Build website
FROM --platform=${BUILDPLATFORM} docker.io/node:22 as web-builder

ENV NODE_ENV=production
WORKDIR /static

COPY web/package.json .
COPY web/package-lock.json .
RUN --mount=type=bind,target=/static/package.json,src=./web/package.json \
    --mount=type=bind,target=/static/package-lock.json,src=./web/package-lock.json \
    --mount=type=cache,target=/root/.npm \
    npm ci --include=dev

COPY web .
RUN npm run build-proxy

# Stage 2: Generate static Go files
FROM --platform=${BUILDPLATFORM} docker.io/openapitools/openapi-generator-cli:v6.5.0 as go-generator

WORKDIR /local

RUN mkdir -p templates && \
    wget https://raw.githubusercontent.com/goauthentik/client-go/main/config.yaml -O ./config.yaml && \
	wget https://raw.githubusercontent.com/goauthentik/client-go/main/templates/README.mustache -O ./templates/README.mustache && \
	wget https://raw.githubusercontent.com/goauthentik/client-go/main/templates/go.mod.mustache -O ./templates/go.mod.mustache

COPY ./schema.yml .

RUN /usr/local/bin/docker-entrypoint.sh generate \
    -i /local/schema.yml -g go -o /local/ -c /local/config.yaml && \
    rm -rf /local/config.yaml /local/templates

# Stage 3: Build
FROM --platform=${BUILDPLATFORM} docker.io/golang:1.22.3-bookworm AS builder

ARG TARGETOS
ARG TARGETARCH
ARG TARGETVARIANT

ARG GOOS=$TARGETOS
ARG GOARCH=$TARGETARCH

WORKDIR /go/src/goauthentik.io

COPY --from=go-generator /local /go/src/goauthentik.io/gen-go-api

COPY ./go.mod /go/src/goauthentik.io/go.mod
COPY ./go.sum /go/src/goauthentik.io/go.sum

RUN --mount=type=cache,target=/go/pkg/mod \
    go mod edit -replace goauthentik.io/api/v3=./gen-go-api && \
    go mod download

ENV CGO_ENABLED=0
COPY . .
RUN --mount=type=cache,sharing=locked,target=/go/pkg/mod \
    --mount=type=cache,id=go-build-$TARGETARCH$TARGETVARIANT,sharing=locked,target=/root/.cache/go-build \
    GOARM="${TARGETVARIANT#v}" go build -o /go/proxy ./cmd/proxy

# Stage 4: Run
FROM gcr.io/distroless/static-debian11:debug

ARG GIT_BUILD_HASH
ENV GIT_BUILD_HASH=$GIT_BUILD_HASH

LABEL org.opencontainers.image.url https://goauthentik.io
LABEL org.opencontainers.image.description goauthentik.io Proxy outpost image, see https://goauthentik.io for more info.
LABEL org.opencontainers.image.source https://github.com/goauthentik/authentik
LABEL org.opencontainers.image.version ${VERSION}
LABEL org.opencontainers.image.revision ${GIT_BUILD_HASH}

COPY --from=builder /go/proxy /
COPY --from=web-builder /static/robots.txt /web/robots.txt
COPY --from=web-builder /static/security.txt /web/security.txt
COPY --from=web-builder /static/dist/ /web/dist/
COPY --from=web-builder /static/authentik/ /web/authentik/

HEALTHCHECK --interval=5s --retries=20 --start-period=3s CMD [ "/proxy", "healthcheck" ]

EXPOSE 9000 9300 9443

USER 1000

ENTRYPOINT ["/proxy"]
