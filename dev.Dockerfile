FROM docker.beryju.org/passbook/base:latest

RUN pipenv lock --dev -r > requirements-dev.txt && \
    pip install -r /app/requirements-dev.txt  --no-cache-dir
