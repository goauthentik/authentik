# Stage 1: Generate API Client
FROM openapitools/openapi-generator-cli as api-builder

COPY ./schema.yml /local/schema.yml

RUN	docker-entrypoint.sh generate \
    --git-host goauthentik.io \
    --git-repo-id outpost \
    --git-user-id api \
    -i /local/schema.yml \
    -g go \
    -o /local/outpost/api \
    --additional-properties=packageName=api,enumClassPrefix=true,useOneOfDiscriminatorLookup=true && \
    rm -f /local/outpost/api/go.mod /local/outpost/api/go.sum

# Stage 2: Build
FROM golang:1.16.4 AS builder
ARG GIT_BUILD_HASH
ENV GIT_BUILD_HASH=$GIT_BUILD_HASH

WORKDIR /go/src/goauthentik.io/outpost

COPY ./outpost .
COPY --from=api-builder /local/outpost/api api

RUN go build -o /go/proxy ./cmd/proxy

# Stage 3: Run
FROM gcr.io/distroless/base-debian10:debug

COPY --from=builder /go/proxy /

HEALTHCHECK CMD [ "wget", "--spider", "http://localhost:4180/akprox/ping" ]

ENTRYPOINT ["/proxy"]
