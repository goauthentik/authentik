FROM python:3.6-slim-stretch as build

COPY ./passbook/ /app/passbook
COPY ./manage.py /app/
COPY ./requirements.txt /app/

WORKDIR /app/

RUN mkdir /app/static/ && \
    pip install -r requirements.txt && \
    pip install psycopg2 && \
    ./manage.py collectstatic --no-input

FROM python:3.6-slim-stretch

COPY ./passbook/ /app/passbook
COPY ./manage.py /app/
COPY ./requirements.txt /app/
COPY --from=build /app/static /app/static/

WORKDIR /app/

RUN pip install -r requirements.txt && \
    pip install psycopg2 && \
    adduser --system --home /app/ passbook && \
    chown -R passbook /app/

USER passbook
