FROM python:3.9-slim-buster as locker

COPY ./Pipfile /app/
COPY ./Pipfile.lock /app/

WORKDIR /app/

RUN pip install pipenv && \
    pipenv lock -r > requirements.txt && \
    pipenv lock -rd > requirements-dev.txt

FROM python:3.9-slim-buster

WORKDIR /
COPY --from=locker /app/requirements.txt /
COPY --from=locker /app/requirements-dev.txt /

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates gnupg && \
    curl https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - && \
    echo "deb http://apt.postgresql.org/pub/repos/apt buster-pgdg main" > /etc/apt/sources.list.d/pgdg.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends postgresql-client-12 postgresql-client-11 build-essential libxmlsec1-dev pkg-config && \
    apt-get clean && \
    pip install -r /requirements.txt --no-cache-dir && \
    apt-get remove --purge -y build-essential && \
    apt-get autoremove --purge -y && \
    # This is quite hacky, but docker has no guaranteed Group ID
    # we could instead check for the GID of the socket and add the user dynamically,
    # but then we have to drop permmissions later
    groupadd -g 998 docker_998 && \
    groupadd -g 999 docker_999 && \
    adduser --system --no-create-home --uid 1000 --group --home /passbook passbook && \
    usermod -a -G docker_998 passbook && \
    usermod -a -G docker_999 passbook && \
    mkdir /backups && \
    chown passbook:passbook /backups

COPY ./passbook/ /passbook
COPY ./pytest.ini /
COPY ./manage.py /
COPY ./lifecycle/ /lifecycle

USER passbook
STOPSIGNAL SIGINT
ENV TMPDIR /dev/shm/
ENTRYPOINT [ "/lifecycle/bootstrap.sh" ]
