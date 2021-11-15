# Stage 1: Build
FROM docker.io/golang:1.17.3-bullseye AS builder

WORKDIR /go/src/goauthentik.io

COPY . .
ENV CGO_ENABLED=0
RUN go build -o /go/ldap ./cmd/ldap

# Stage 2: Run
FROM gcr.io/distroless/static-debian11:debug

ARG GIT_BUILD_HASH
ENV GIT_BUILD_HASH=$GIT_BUILD_HASH

COPY --from=builder /go/ldap /

HEALTHCHECK CMD [ "wget", "--spider", "http://localhost:9300/akprox/ping" ]

EXPOSE 3389 6636 9300

ENTRYPOINT ["/ldap"]
