FROM python:3.8-slim-buster as locker

COPY ./Pipfile /app/
COPY ./Pipfile.lock /app/

WORKDIR /app/

RUN pip install pipenv && \
    pipenv lock -r > requirements.txt && \
    pipenv lock -rd > requirements-dev.txt

FROM python:3.8-slim-buster

WORKDIR /
COPY --from=locker /app/requirements.txt /
COPY --from=locker /app/requirements-dev.txt /

RUN apt-get update && \
    apt-get install -y --no-install-recommends postgresql-client-11 build-essential && \
    apt-get clean && \
    pip install -r /requirements.txt --no-cache-dir && \
    apt-get remove --purge -y build-essential && \
    apt-get autoremove --purge -y && \
    adduser --system --no-create-home --uid 1000 --group --home /passbook passbook

COPY ./passbook/ /passbook
COPY ./manage.py /
COPY ./lifecycle/ /lifecycle

USER passbook

ENTRYPOINT [ "/lifecycle/bootstrap.sh" ]
