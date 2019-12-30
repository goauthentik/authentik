FROM beryju/passbook-base:latest

COPY ./passbook/ /app/passbook
COPY ./manage.py /app/
COPY ./docker/uwsgi.ini /app/

WORKDIR /app/

USER passbook
