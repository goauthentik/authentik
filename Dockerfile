FROM python:3.6-slim-stretch as build

COPY ./passbook/ /app/passbook
COPY ./manage.py /app/
COPY ./requirements.txt /app/

WORKDIR /app/

RUN apt-get update && apt-get install build-essential libssl-dev libffi-dev -y && \
    mkdir /app/static/ && \
    pip install -r requirements.txt && \
    pip install psycopg2 && \
    ./manage.py collectstatic --no-input && \
    apt-get remove --purge -y build-essential && \
    apt-get autoremove --purge -y

FROM python:3.6-slim-stretch

COPY ./passbook/ /app/passbook
COPY ./manage.py /app/
COPY ./requirements.txt /app/
COPY --from=build /app/static /app/static/

WORKDIR /app/

RUN apt-get update && apt-get install build-essential libssl-dev libffi-dev -y && \
    pip install -r requirements.txt && \
    pip install psycopg2 && \
    adduser --system --home /app/ passbook && \
    chown -R passbook /app/ && \
    apt-get remove --purge -y build-essential && \
    apt-get autoremove --purge -y

USER passbook
