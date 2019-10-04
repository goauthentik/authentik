FROM docker.beryju.org/passbook/base:latest

RUN pipenv lock --dev -r > requirements-dev.txt && \
    pipenv --rm && \
    pip install -r /app/requirements-dev.txt  --no-cache-dir
