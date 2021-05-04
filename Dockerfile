# Stage 1: Lock python dependencies
FROM python:3.9-slim-buster as locker

COPY ./Pipfile /app/
COPY ./Pipfile.lock /app/

WORKDIR /app/

RUN pip install pipenv && \
    pipenv lock -r > requirements.txt && \
    pipenv lock -rd > requirements-dev.txt

# Stage 2: Build webui
FROM node as npm-builder

COPY ./web /static/

ENV NODE_ENV=production
RUN cd /static && npm i --production=false && npm run build

# Stage 3: Build go proxy
FROM golang:1.16.3 AS builder

WORKDIR /work

COPY --from=npm-builder /static/robots.txt /work/web/robots.txt
COPY --from=npm-builder /static/security.txt /work/web/security.txt
COPY --from=npm-builder /static/dist/ /work/web/dist/
COPY --from=npm-builder /static/authentik/ /work/web/authentik/

# RUN ls /work/web/static/authentik/ && exit 1
COPY ./cmd /work/cmd
COPY ./web/static.go /work/web/static.go
COPY ./internal /work/internal
COPY ./go.mod /work/go.mod
COPY ./go.sum /work/go.sum

RUN go build -o /work/authentik ./cmd/server/main.go

# Stage 4: Run
FROM python:3.9-slim-buster

WORKDIR /
COPY --from=locker /app/requirements.txt /
COPY --from=locker /app/requirements-dev.txt /

ARG GIT_BUILD_HASH
ENV GIT_BUILD_HASH=$GIT_BUILD_HASH

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates gnupg && \
    curl https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - && \
    echo "deb http://apt.postgresql.org/pub/repos/apt buster-pgdg main" > /etc/apt/sources.list.d/pgdg.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends postgresql-client-12 postgresql-client-11 build-essential libxmlsec1-dev pkg-config libmaxminddb0 && \
    apt-get clean && \
    pip install -r /requirements.txt --no-cache-dir && \
    apt-get remove --purge -y build-essential && \
    apt-get autoremove --purge -y && \
    # This is quite hacky, but docker has no guaranteed Group ID
    # we could instead check for the GID of the socket and add the user dynamically,
    # but then we have to drop permmissions later
    groupadd -g 998 docker_998 && \
    groupadd -g 999 docker_999 && \
    adduser --system --no-create-home --uid 1000 --group --home /authentik authentik && \
    usermod -a -G docker_998 authentik && \
    usermod -a -G docker_999 authentik && \
    mkdir /backups && \
    chown authentik:authentik /backups

COPY ./authentik/ /authentik
COPY ./pyproject.toml /
COPY ./xml /xml
COPY ./manage.py /
COPY ./lifecycle/ /lifecycle
COPY --from=builder /work/authentik /authentik-proxy

USER authentik
STOPSIGNAL SIGINT
ENV TMPDIR /dev/shm/
ENV PYTHONUBUFFERED 1
ENTRYPOINT [ "/lifecycle/bootstrap.sh" ]
