FROM docker.beryju.org/passbook/dev:latest as static-build

COPY ./passbook/ /app/passbook
COPY ./manage.py /app/

WORKDIR /app/

ENV PASSBOOK_POSTGRESQL__USER=passbook
# CI Password, same as in .gitlab-ci.yml
ENV PASSBOOK_POSTGRESQL__PASSWORD="EK-5jnKfjrGRm<77"
RUN ./manage.py collectstatic --no-input

FROM nginx:latest

COPY --from=static-build /app/static /data/static/
COPY --from=static-build /app/static/robots.txt /data/robots.txt
COPY ./passbook/core/nginx.conf /etc/nginx/nginx.conf
