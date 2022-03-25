# Stage 1: Build website
FROM --platform=${BUILDPLATFORM} docker.io/node:16 as website-builder

COPY ./website /work/website/

ENV NODE_ENV=production
RUN cd /work/website && npm i && npm run build-docs-only

# Stage 2: Build webui
FROM --platform=${BUILDPLATFORM} docker.io/node:16 as web-builder

COPY ./web /work/web/
COPY ./website /work/website/

ENV NODE_ENV=production
RUN cd /work/web && npm i && npm run build

# Stage 3: Build go proxy
FROM docker.io/golang:1.18.0-bullseye AS builder

WORKDIR /work

COPY --from=web-builder /work/web/robots.txt /work/web/robots.txt
COPY --from=web-builder /work/web/security.txt /work/web/security.txt

COPY ./cmd /work/cmd
COPY ./web/static.go /work/web/static.go
COPY ./internal /work/internal
COPY ./go.mod /work/go.mod
COPY ./go.sum /work/go.sum

RUN go build -o /work/authentik ./cmd/server/main.go

# Stage 4: Run
FROM docker.io/python:3.10.4-slim-bullseye

LABEL org.opencontainers.image.url https://goauthentik.io
LABEL org.opencontainers.image.description goauthentik.io Main server image, see https://goauthentik.io for more info.
LABEL org.opencontainers.image.source https://github.com/goauthentik/authentik

WORKDIR /

ARG GIT_BUILD_HASH
ENV GIT_BUILD_HASH=$GIT_BUILD_HASH

COPY ./pyproject.toml /
COPY ./poetry.lock /

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl ca-certificates gnupg git runit libpq-dev \
        postgresql-client build-essential libxmlsec1-dev \
        pkg-config libmaxminddb0 && \
    pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev && \
    rm -rf ~/.cache/pypoetry && \
    apt-get remove --purge -y build-essential git && \
    apt-get autoremove --purge -y && \
    apt-get clean && \
    rm -rf /tmp/* /var/lib/apt/lists/* /var/tmp/ && \
    adduser --system --no-create-home --uid 1000 --group --home /authentik authentik && \
    mkdir -p /certs /media && \
    mkdir -p /authentik/.ssh && \
    chown authentik:authentik /certs /media /authentik/.ssh

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
