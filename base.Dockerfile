FROM python:3.7-slim-stretch

COPY ./Pipfile /app/
COPY ./Pipfile.lock /app/

WORKDIR /app/

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    pip install pipenv uwsgi --no-cache-dir && \
    apt-get remove -y --purge build-essential && \
    apt-get autoremove -y --purge && \
    rm -rf /var/lib/apt/lists/*

RUN pipenv lock -r > requirements.txt && \
    pipenv --rm && \
    pip install -r requirements.txt  --no-cache-dir && \
    adduser --system --no-create-home passbook && \
    chown -R passbook /app
