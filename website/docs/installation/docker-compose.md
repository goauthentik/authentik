---
title: docker-compose installation
---

This installation method is for test-setups and small-scale productive setups.

## Prerequisites

-   docker
-   docker-compose

## Preparation

Download the latest `docker-compose.yml` from [here](https://raw.githubusercontent.com/BeryJu/authentik/master/docker-compose.yml). Place it in a directory of your choice.

To optionally enable error-reporting, run `echo AUTHENTIK_ERROR_REPORTING__ENABLED=true >> .env`

To optionally deploy a different version run `echo AUTHENTIK_TAG=0.14.2-stable >> .env`

If this is a fresh authentik install run the following commands to generate a password:

```
sudo apt-get install -y pwgen
echo "PG_PASS=$(pwgen 40 1)" >> .env
echo "AUTHENTIK_SECRET_KEY=$(pwgen 50 1)" >> .env
```

## Email configuration (optional, but recommended)

It is also recommended to configure global email credentials. These are used by authentik to notify you about alerts, configuration issues. They can also be used by [Email stages](flow/stages/email/index.md) to send verification/recovery emails.

Append this block to your `.env` file

```
# SMTP Host Emails are sent to
AUTHENTIK_EMAIL__HOST=localhost
AUTHENTIK_EMAIL__PORT=25
# Optionally authenticate
AUTHENTIK_EMAIL__USERNAME=""
AUTHENTIK_EMAIL__PASSWORD=""
# Use StartTLS
AUTHENTIK_EMAIL__USE_TLS=false
# Use SSL
AUTHENTIK_EMAIL__USE_SSL=false
AUTHENTIK_EMAIL__TIMEOUT=10
# Email address authentik will send from, should have a correct @domain
AUTHENTIK_EMAIL__FROM=authentik@localhost
```

## Startup

Afterwards, run these commands to finish

```
docker-compose pull
docker-compose up -d
docker-compose run --rm server migrate
```

The compose file statically references the latest version available at the time of downloading, which can be overridden with the `SERVER_TAG` environment variable.

If you plan to use this setup for production, it is also advised to change the PostgreSQL password by setting `PG_PASS` to a password of your choice.

Now you can pull the Docker images needed by running `docker-compose pull`. After this has finished, run `docker-compose up -d` to start authentik.

authentik will then be reachable HTTPS on port 443. You can optionally configure the packaged traefik to use Let's Encrypt certificates for TLS Encryption.

The initial setup process also creates a default admin user, the username and password for which is `akadmin`. It is highly recommended to change this password as soon as you log in.
