---
title: docker-compose installation
---

This installation method is for test-setups and small-scale productive setups.

## Requirements

-   A Linux host with at least 2 CPU cores and 2 GB of RAM.
-   docker
-   docker-compose

## Preparation

Download the latest `docker-compose.yml` from [here](https://goauthentik.io/docker-compose.yml). Place it in a directory of your choice.

If this is a fresh authentik install run the following commands to generate a password:

```shell
# You can also use openssl instead: `openssl rand -base64 36`
sudo apt-get install -y pwgen
# Because of a PostgreSQL limitation, only passwords up to 99 chars are supported
# See https://www.postgresql.org/message-id/09512C4F-8CB9-4021-B455-EF4C4F0D55A0@amazon.com
echo "PG_PASS=$(pwgen -s 40 1)" >> .env
echo "AUTHENTIK_SECRET_KEY=$(pwgen -s 50 1)" >> .env
# Skip if you don't want to enable error reporting
echo "AUTHENTIK_ERROR_REPORTING__ENABLED=true" >> .env
```

## Email configuration (optional, but recommended)

It is also recommended to configure global email credentials. These are used by authentik to notify you about alerts and configuration issues. They can also be used by [Email stages](../flow/stages/email/) to send verification/recovery emails.

Append this block to your `.env` file

```shell
# SMTP Host Emails are sent to
AUTHENTIK_EMAIL__HOST=localhost
AUTHENTIK_EMAIL__PORT=25
# Optionally authenticate (don't add quotation marks to you password)
AUTHENTIK_EMAIL__USERNAME=
AUTHENTIK_EMAIL__PASSWORD=
# Use StartTLS
AUTHENTIK_EMAIL__USE_TLS=false
# Use SSL
AUTHENTIK_EMAIL__USE_SSL=false
AUTHENTIK_EMAIL__TIMEOUT=10
# Email address authentik will send from, should have a correct @domain
AUTHENTIK_EMAIL__FROM=authentik@localhost
```

## GeoIP configuration (optional)

authentik can use a MaxMind-formatted GeoIP Database to extract location data from IPs. You can then use this location data in policies, and location data is saved in events.

To configure GeoIP, sign up for a free MaxMind account [here](https://www.maxmind.com/en/geolite2/signup).

After you have your account ID and license key, add the following block to your `.env` file:

```shell
GEOIPUPDATE_ACCOUNT_ID=*your account ID*
GEOIPUPDATE_LICENSE_KEY=* your license key*
AUTHENTIK_AUTHENTIK__GEOIP=/geoip/GeoLite2-City.mmdb
```

The GeoIP database will automatically be updated every 8 hours.

## Running on Port 80/443

By default, authentik listens on port 9000 for HTTP and 9443 for HTTPS. To change this, you can set the following variables in `.env`:

```shell
AUTHENTIK_PORT_HTTP=80
AUTHENTIK_PORT_HTTPS=443
```

Afterwards, make sure to run `docker-compose up -d`.

## Startup

Afterwards, run these commands to finish

```shell
docker-compose pull
docker-compose up -d
```

The compose file statically references the latest version available at the time of downloading the compose file, which can be overridden with the `AUTHENTIK_TAG` environment variable.

authentik will then be reachable on port 9000 (HTTP) and port 9443 (HTTPS).

To start the initial setup, navigate to `https://<your server>/if/flow/initial-setup/`. There you will be prompted to set a password for the akadmin user.

## Explanation

:::warning
The server assumes to have local timezone as UTC.
All internals are handled in UTC, whenever a time is displayed to the user in UI it gets localized.
Do not update or mount `/etc/timezone` or `/etc/localtime` in the authentik containers.
This will not give any advantages.
On the contrary, it will cause problems with OAuth and SAML authentication,
e.g. [see this GitHub issue](https://github.com/goauthentik/authentik/issues/3005).
:::

The docker-compose project contains the following containers:

-   server

    This is the backend service, which does all the logic, runs the API and the actual SSO part. It also runs the frontend, hosts the JS/CSS files, and also serves the files you've uploaded for icons/etc.

-   worker

    This container executes background tasks, everything you can see on the _System Tasks_ page in the frontend.

-   redis & postgresql

    Cache and database respectively.

Additionally, if you've enabled GeoIP, there is a container running that regularly updates the GeoIP database.
