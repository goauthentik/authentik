# Stage 1: Lock python dependencies
FROM python:3.9-slim-buster as locker

COPY ./Pipfile /app/
COPY ./Pipfile.lock /app/

WORKDIR /app/

RUN pip install pipenv && \
    pipenv lock -r > requirements.txt && \
    pipenv lock -rd > requirements-dev.txt

# Stage 2: Build web API
FROM openapitools/openapi-generator-cli as api-builder

COPY ./schema.yml /local/schema.yml

RUN	docker-entrypoint.sh generate \
    -i /local/schema.yml \
    -g typescript-fetch \
    -o /local/web/api \
    --additional-properties=typescriptThreePlus=true,supportsES6=true,npmName=authentik-api,npmVersion=1.0.0

# Stage 3: Build webui
FROM node as npm-builder

COPY ./web /static/
COPY --from=api-builder /local/web/api /static/web/api

ENV NODE_ENV=production
RUN cd /static && npm i --production=false && npm run build

# Stage 4: Build go proxy
FROM golang:1.16.4 AS builder

WORKDIR /work

COPY --from=npm-builder /static/robots.txt /work/web/robots.txt
COPY --from=npm-builder /static/security.txt /work/web/security.txt
COPY --from=npm-builder /static/dist/ /work/web/dist/
COPY --from=npm-builder /static/authentik/ /work/web/authentik/

COPY ./cmd /work/cmd
COPY ./web/static.go /work/web/static.go
COPY ./internal /work/internal
COPY ./go.mod /work/go.mod
COPY ./go.sum /work/go.sum

RUN go build -o /work/authentik ./cmd/server/main.go

# Stage 5: Run
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
COPY ./manage.py /
COPY ./lifecycle/ /lifecycle
COPY --from=builder /work/authentik /authentik-proxy

USER authentik
ENV TMPDIR /dev/shm/
ENV PYTHONUBUFFERED 1
ENTRYPOINT [ "/lifecycle/bootstrap.sh" ]
