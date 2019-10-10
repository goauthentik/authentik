FROM docker.beryju.org/passbook/base:latest

COPY --chown=passbook:passbook ./passbook/ /app/passbook
COPY ./manage.py /app/
COPY ./docker/uwsgi.ini /app/

WORKDIR /app/

USER passbook
