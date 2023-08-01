# Stage 1: Build
FROM docker.io/golang:1.20.6-bullseye AS builder

WORKDIR /go/src/goauthentik.io

COPY . .
ENV CGO_ENABLED=0
RUN go build -o /go/kerberos ./cmd/kerberos

# Stage 2: Run
FROM gcr.io/distroless/static-debian11:debug

ARG GIT_BUILD_HASH
ENV GIT_BUILD_HASH=$GIT_BUILD_HASH

LABEL org.opencontainers.image.url https://goauthentik.io
LABEL org.opencontainers.image.description goauthentik.io Kerberos outpost, see https://goauthentik.io for more info.
LABEL org.opencontainers.image.source https://github.com/goauthentik/authentik
LABEL org.opencontainers.image.version ${VERSION}
LABEL org.opencontainers.image.revision ${GIT_BUILD_HASH}

COPY --from=builder /go/kerberos /

HEALTHCHECK --interval=5s --retries=20 --start-period=3s CMD [ "/kerberos", "healthcheck" ]

EXPOSE 8888/tcp 8888/udp 9300/tcp

USER 1000

ENTRYPOINT ["/kerberos"]
