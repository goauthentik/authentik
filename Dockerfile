FROM python:3.6-slim-stretch
# LABEL version="1.8.8"

COPY ./passbook/ /app/passbook
COPY ./static/ /app/static
COPY ./manage.py /app/
COPY ./requirements.txt /app/

WORKDIR /app/

#RUN apk add --no-cache libffi-dev build-base py2-pip python2-dev libxml-dev && \
RUN pip install -r requirements.txt && \
    pip install psycopg2 && \
    adduser --system --home /app/ passbook && \
    chown -R passbook /app/

USER passbook
