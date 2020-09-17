# docker-compose

This installation method is for test-setups and small-scale productive setups.

## Prerequisites

-   docker
-   docker-compose

## Install

Download the latest `docker-compose.yml` from [here](https://raw.githubusercontent.com/BeryJu/passbook/master/docker-compose.yml). Place it in a directory of your choice.

To optionally enable error-reporting, run `echo PASSBOOK_ERROR_REPORTING=true >> .env`

To optionally deploy a different version run `echo PASSBOOK_TAG=0.10.3-stable >> .env`

If this is a fresh passbook install run the following commands to generate a password:

```
sudo apt-get install -y pwgen
echo "PG_PASS=$(pwgen 40 1)" >> .env
echo "PASSBOOK_SECRET_KEY=$(pwgen 50 1)" >> .env
```

Afterwards, run these commands to finish

```
docker-compose pull
docker-compose up -d
docker-compose run --rm server migrate
```

The compose file statically references the latest version available at the time of downloading, which can be overridden with the `SERVER_TAG` environment variable.

If you plan to use this setup for production, it is also advised to change the PostgreSQL password by setting `PG_PASS` to a password of your choice.

Now you can pull the Docker images needed by running `docker-compose pull`. After this has finished, run `docker-compose up -d` to start passbook.

passbook will then be reachable via HTTP on port 80, and HTTPS on port 443. You can optionally configure the packaged traefik to use Let's Encrypt certificates for TLS Encryption.

The initial setup process also creates a default admin user, the username and password for which is `pbadmin`. It is highly recommended to change this password as soon as you log in.
