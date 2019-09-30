FROM python:3.7-alpine

COPY ./Pipfile /app/
COPY ./Pipfile.lock /app/

WORKDIR /app/

RUN apk update && \
    apk add --no-cache openssl-dev build-base libxml2-dev libxslt-dev libffi-dev gcc musl-dev libgcc zlib-dev postgresql-dev && \
    pipenv lock -r > requirements.txt && \
    pip install -r requirements.txt  --no-cache-dir && \
    adduser -S passbook && \
    chown -R passbook /app
