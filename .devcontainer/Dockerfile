FROM ghcr.io/goauthentik/server:latest

USER root

HEALTHCHECK --interval=10s CMD exit 0

RUN pip install --no-cache-dir -r /app-root/requirements-dev.txt
