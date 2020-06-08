# docker-compose

This installation Method is for test-setups and small-scale productive setups.

## Prerequisites

-   docker
-   docker-compose

## Install

```
wget https://raw.githubusercontent.com/BeryJu/passbook/master/docker-compose.yml
# Optionally enable Error-reporting
# export PASSBOOK_ERROR_REPORTING=true
# Optionally deploy a different version
# export PASSBOOK_TAG=0.8.15-beta
# If this is a productive installation, set a different PostgreSQL Password
# export PG_PASS=$(pwgen 40 1)
docker-compose pull
docker-compose up -d
docker-compose exec server ./manage.py migrate
```

Afterwards, you can log in using `pbadmin` as username and password.
