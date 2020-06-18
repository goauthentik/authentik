# docker-compose

This installation method is for test-setups and small-scale productive setups.

## Prerequisites

-   docker
-   docker-compose

## Install

Download the latest `docker-compose.yml` from [here](https://raw.githubusercontent.com/BeryJu/passbook/master/docker-compose.yml). Place it in a directory of your choice.

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

The compose file references the current latest version, which can be overridden with the `SERVER_TAG` environment variable.

If you plan to use this setup for production, it is also advised to change the PostgreSQL password by setting `PG_PASS` to a password of your choice.

Now you can pull the Docker images needed by running `docker-compose pull`. After this has finished, run `docker-compose up -d` to start passbook.

passbook will then be reachable via HTTP on port 80, and HTTPS on port 443. You can optionally configure the packaged traefik to use Let's Encrypt certificates for TLS Encryption.

The initial setup also creates a default admin user called `pbadmin` with the same password. It is highly recommended to change this password as soon as you log in.
