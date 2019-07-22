FROM docker.beryju.org/passbook/base:latest

COPY ./passbook/ /app/passbook
COPY ./manage.py /app/

USER passbook

WORKDIR /app/
