FROM python:3.7-slim-buster as locker

COPY ./Pipfile /app/
COPY ./Pipfile.lock /app/

WORKDIR /app/

RUN pip install pipenv && \
    pipenv lock -r > requirements.txt && \
    pipenv lock -rd > requirements-dev.txt

FROM python:3.7-slim-buster as static-build

COPY --from=locker /app/requirements.txt /app/
COPY --from=locker /app/requirements-dev.txt /app/

WORKDIR /app/

RUN apt-get update && \
    apt-get install -y --no-install-recommends postgresql-client-11 && \
    rm -rf /var/lib/apt/ && \
    pip install -r requirements.txt  --no-cache-dir && \
    adduser --system --no-create-home --uid 1000 --group --home /app passbook

COPY ./passbook/ /app/passbook
COPY ./manage.py /app/

WORKDIR /app/

ENV PASSBOOK_POSTGRESQL__HOST=postgres
ENV PASSBOOK_REDIS__HOST=redis
ENV PASSBOOK_POSTGRESQL__USER=passbook
# CI Password, same as in .github/workflows/ci.yml
ENV PASSBOOK_POSTGRESQL__PASSWORD="EK-5jnKfjrGRm<77"
RUN ./manage.py collectstatic --no-input

FROM docker.beryju.org/pixie/server

COPY --from=static-build /app/static /data/static/
COPY --from=static-build /app/static/robots.txt /data/robots.txt
WORKDIR /data
