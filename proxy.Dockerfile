# Stage 1: Build website
FROM --platform=${BUILDPLATFORM} docker.io/node:20 as web-builder

COPY ./web /static/

ENV NODE_ENV=production
WORKDIR /static
RUN npm ci --include=dev && npm run build-proxy

# Stage 2: Build
FROM docker.io/golang:1.20.5-bullseye AS builder

WORKDIR /go/src/goauthentik.io

COPY . .

ENV CGO_ENABLED=0
RUN go build -o /go/proxy ./cmd/proxy

# Stage 3: Run
FROM gcr.io/distroless/static-debian11:debug

LABEL org.opencontainers.image.url https://goauthentik.io
LABEL org.opencontainers.image.description goauthentik.io Proxy outpost image, see https://goauthentik.io for more info.
LABEL org.opencontainers.image.source https://github.com/goauthentik/authentik

ARG GIT_BUILD_HASH
ENV GIT_BUILD_HASH=$GIT_BUILD_HASH

COPY --from=builder /go/proxy /
COPY --from=web-builder /static/robots.txt /web/robots.txt
COPY --from=web-builder /static/security.txt /web/security.txt
COPY --from=web-builder /static/dist/ /web/dist/
COPY --from=web-builder /static/authentik/ /web/authentik/

HEALTHCHECK --interval=5s --retries=20 --start-period=3s CMD [ "/proxy", "healthcheck" ]

EXPOSE 9000 9300 9443

USER 1000

ENTRYPOINT ["/proxy"]
