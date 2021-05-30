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
    --additional-properties=packageName=api,enumClassPrefix=true,useOneOfDiscriminatorLookup=true

# Stage 2: Build
FROM golang:1.16.4 AS builder
ARG GIT_BUILD_HASH
ENV GIT_BUILD_HASH=$GIT_BUILD_HASH

WORKDIR /work

COPY ./outpost .
COPY --from=api-builder /local/outpost/api /work/outpost/api

RUN go build -o /work/ldap ./cmd/ldap

# Stage 3: Run
FROM gcr.io/distroless/base-debian10:debug

COPY --from=builder /work/ldap /

ENTRYPOINT ["/ldap"]
