# Stage 1: Generate API Client
FROM openapitools/openapi-generator-cli as api-builder

COPY ./schema.yml /local/schema.yml

RUN	docker-entrypoint.sh generate \
    --git-host goauthentik.io \
    --git-repo-id outpost \
    --git-user-id api \
    -i /local/schema.yml \
    -g go \
    -o /local/api \
    --additional-properties=packageName=api,enumClassPrefix=true,useOneOfDiscriminatorLookup=true && \
    rm -f /local/api/go.mod /local/api/go.sum

# Stage 2: Build website
FROM node as web-builder

COPY ./web /static/

ENV NODE_ENV=production
RUN cd /static && npm i && npm run build

# Stage 2: Build
FROM golang:1.17.0 AS builder

WORKDIR /go/src/goauthentik.io

COPY . .
COPY --from=web-builder /static/robots.txt /work/web/robots.txt
COPY --from=web-builder /static/security.txt /work/web/security.txt
COPY --from=web-builder /static/dist/ /work/web/dist/
COPY --from=web-builder /static/authentik/ /work/web/authentik/
COPY --from=api-builder /local/api api

RUN go build -o /go/proxy ./cmd/proxy

# Stage 3: Run
FROM gcr.io/distroless/base-debian10:debug

ARG GIT_BUILD_HASH
ENV GIT_BUILD_HASH=$GIT_BUILD_HASH

COPY --from=builder /go/proxy /

HEALTHCHECK CMD [ "wget", "--spider", "http://localhost:9100/akprox/ping" ]

ENTRYPOINT ["/proxy"]
