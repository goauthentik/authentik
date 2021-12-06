# Stage 1: Lock python dependencies
FROM docker.io/python:3.9-slim-bullseye as locker

COPY ./Pipfile /app/
COPY ./Pipfile.lock /app/

WORKDIR /app/

RUN pip install pipenv && \
    pipenv lock -r > requirements.txt && \
    pipenv lock -r --dev-only > requirements-dev.txt

# Stage 2: Build website
FROM --platform=${BUILDPLATFORM} docker.io/node:16 as website-builder

COPY ./website /work/website/

ENV NODE_ENV=production
RUN cd /work/website && npm i && npm run build-docs-only

# Stage 3: Build webui
FROM --platform=${BUILDPLATFORM} docker.io/node:16 as web-builder

COPY ./web /work/web/
COPY ./website /work/website/

ENV NODE_ENV=production
RUN cd /work/web && npm i && npm run build

# Stage 4: Build go proxy
FROM docker.io/golang:1.17.4-bullseye AS builder

WORKDIR /work

COPY --from=web-builder /work/web/robots.txt /work/web/robots.txt
COPY --from=web-builder /work/web/security.txt /work/web/security.txt

COPY ./cmd /work/cmd
COPY ./web/static.go /work/web/static.go
COPY ./internal /work/internal
COPY ./go.mod /work/go.mod
COPY ./go.sum /work/go.sum

RUN go build -o /work/authentik ./cmd/server/main.go

# Stage 5: Run
FROM docker.io/python:3.9-slim-bullseye

WORKDIR /
COPY --from=locker /app/requirements.txt /
COPY --from=locker /app/requirements-dev.txt /

ARG GIT_BUILD_HASH
ENV GIT_BUILD_HASH=$GIT_BUILD_HASH

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl ca-certificates gnupg git runit libpq-dev \
        postgresql-client build-essential libxmlsec1-dev \
        pkg-config libmaxminddb0 && \
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
COPY --from=web-builder /work/web/dist/ /web/dist/
COPY --from=web-builder /work/web/authentik/ /web/authentik/
COPY --from=website-builder /work/website/help/ /website/help/

USER authentik

ENV TMPDIR /dev/shm/
ENV PYTHONUNBUFFERED 1
ENV PATH "/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/lifecycle"

HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 CMD [ "/lifecycle/ak", "healthcheck" ]

ENTRYPOINT [ "/lifecycle/ak" ]
