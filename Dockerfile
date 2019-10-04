FROM docker.beryju.org/passbook/base:latest

COPY ./passbook/ /app/passbook
COPY ./manage.py /app/
COPY ./docker/uwsgi.ini /app/

USER passbook

WORKDIR /app/
