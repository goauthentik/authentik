# docker-compose

This installation method is for test-setups and small-scale productive setups.

## Prerequisites

-   docker
-   docker-compose

## Install

Download the latest `docker-compose.yml` from [here](https://raw.githubusercontent.com/BeryJu/passbook/master/docker-compose.yml). Place it in a directory of your choice.

passbook needs to know it's primary URL to create links in e-mails and set cookies, so you have to run the following command:

```
export PASSBOOK_DOMAIN=domain.tld # this can be any domain or IP, it just needs to point to passbook.
```

The compose file references the current latest version, which can be overridden with the `SERVER_TAG` environment variable.

If you plan to use this setup for production, it is also advised to change the PostgreSQL password by setting `PG_PASS` to a password of your choice.

Now you can pull the Docker images needed by running `docker-compose pull`. After this has finished, run `docker-compose up -d` to start passbook.

passbook will then be reachable on port 80. You can optionally configure the packaged traefik to use Let's Encrypt certificates for TLS Encryption.
