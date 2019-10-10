FROM python:3.7-slim-buster as locker

COPY ./Pipfile /app/
COPY ./Pipfile.lock /app/

WORKDIR /app/

RUN pip install pipenv && \
    pipenv lock -r > requirements.txt && \
    pipenv lock -rd > requirements-dev.txt

FROM python:3.7-slim-buster

COPY --from=locker /app/requirements.txt /app/

WORKDIR /app/

RUN pip install -r requirements.txt  --no-cache-dir && \
    adduser --system --no-create-home --uid 1000 --group --home /app passbook
