FROM python:3.8-slim-buster as locker

COPY ./Pipfile /app/
COPY ./Pipfile.lock /app/

WORKDIR /app/

RUN pip install pipenv && \
    pipenv lock -r > requirements.txt && \
    pipenv lock -rd > requirements-dev.txt

FROM python:3.8-slim-buster

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
COPY ./docker/uwsgi.ini /app/

WORKDIR /app/

USER passbook
