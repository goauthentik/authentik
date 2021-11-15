# Stage 1: Build website
FROM docker.io/node:16 as web-builder

COPY ./web /static/

ENV NODE_ENV=production
RUN cd /static && npm i && npm run build

# Stage 2: Build
FROM docker.io/golang:1.17.3-bullseye AS builder

WORKDIR /go/src/goauthentik.io

COPY . .
COPY --from=web-builder /static/robots.txt /work/web/robots.txt
COPY --from=web-builder /static/security.txt /work/web/security.txt
COPY --from=web-builder /static/dist/ /work/web/dist/
COPY --from=web-builder /static/authentik/ /work/web/authentik/

ENV CGO_ENABLED=0
RUN go build -o /go/proxy ./cmd/proxy

# Stage 3: Run
FROM gcr.io/distroless/static-debian11:debug

ARG GIT_BUILD_HASH
ENV GIT_BUILD_HASH=$GIT_BUILD_HASH

COPY --from=builder /go/proxy /

HEALTHCHECK CMD [ "wget", "--spider", "http://localhost:9300/akprox/ping" ]

EXPOSE 9000 9300 9443

ENTRYPOINT ["/proxy"]
