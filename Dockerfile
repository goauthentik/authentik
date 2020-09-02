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
    apt-get install -y --no-install-recommends postgresql-client-11 build-essential && \
    rm -rf /var/lib/apt/ && \
    pip install -r requirements.txt  --no-cache-dir && \
    apt-get remove --purge -y build-essential && \
    apt-get autoremove --purge && \
    adduser --system --no-create-home --uid 1000 --group --home /app passbook

COPY ./passbook/ /app/passbook
COPY ./manage.py /app/
COPY ./docker/gunicorn.conf.py /app/
COPY ./docker/bootstrap.sh /bootstrap.sh
COPY ./docker/wait_for_db.py /app/wait_for_db.py

WORKDIR /app/

USER passbook

ENTRYPOINT [ "/bootstrap.sh" ]
