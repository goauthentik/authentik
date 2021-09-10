# Stage 1: Lock python dependencies
FROM python:3.9-slim-buster as locker

COPY ./Pipfile /app/
COPY ./Pipfile.lock /app/

WORKDIR /app/

RUN pip install pipenv && \
    pipenv lock -r > requirements.txt && \
    pipenv lock -r --dev-only > requirements-dev.txt

# Stage 2: Build website
FROM node as website-builder

COPY ./website /static/

ENV NODE_ENV=production
RUN cd /static && npm i && npm run build-docs-only

# Stage 3: Generate API Client
FROM openapitools/openapi-generator-cli as go-api-builder

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

# Stage 4: Build webui
FROM node as web-builder

COPY ./web /static/

ENV NODE_ENV=production
RUN cd /static && npm i && npm run build

# Stage 5: Build go proxy
FROM golang:1.17.1 AS builder

WORKDIR /work

COPY --from=web-builder /static/robots.txt /work/web/robots.txt
COPY --from=web-builder /static/security.txt /work/web/security.txt
COPY --from=web-builder /static/dist/ /work/web/dist/
COPY --from=web-builder /static/authentik/ /work/web/authentik/
COPY --from=website-builder /static/help/ /work/website/help/

COPY --from=go-api-builder /local/api api
COPY ./cmd /work/cmd
COPY ./web/static.go /work/web/static.go
COPY ./website/static.go /work/website/static.go
COPY ./internal /work/internal
COPY ./go.mod /work/go.mod
COPY ./go.sum /work/go.sum

RUN go build -o /work/authentik ./cmd/server/main.go

# Stage 6: Run
FROM python:3.9-slim-buster

WORKDIR /
COPY --from=locker /app/requirements.txt /
COPY --from=locker /app/requirements-dev.txt /

ARG GIT_BUILD_HASH
ENV GIT_BUILD_HASH=$GIT_BUILD_HASH

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates gnupg git runit && \
    curl https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - && \
    echo "deb http://apt.postgresql.org/pub/repos/apt buster-pgdg main" > /etc/apt/sources.list.d/pgdg.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends libpq-dev postgresql-client build-essential libxmlsec1-dev pkg-config libmaxminddb0 && \
    pip install -r /requirements.txt --no-cache-dir && \
    apt-get remove --purge -y build-essential git && \
    apt-get autoremove --purge -y && \
    apt-get clean && \
    rm -rf /tmp/* /var/lib/apt/lists/* /var/tmp/ && \
    adduser --system --no-create-home --uid 1000 --group --home /authentik authentik && \
    mkdir /backups && \
    chown authentik:authentik /backups

COPY ./authentik/ /authentik
COPY ./pyproject.toml /
COPY ./xml /xml
COPY ./tests /tests
COPY ./manage.py /
COPY ./lifecycle/ /lifecycle
COPY --from=builder /work/authentik /authentik-proxy

USER authentik
ENV TMPDIR /dev/shm/
ENV PYTHONUBUFFERED 1
ENV prometheus_multiproc_dir /dev/shm/
ENV PATH "/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/lifecycle"
ENTRYPOINT [ "/lifecycle/ak" ]
