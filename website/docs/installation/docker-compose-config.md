---
title: docker-compose configuration
---

These are all the configuration options you can set via docker-compose. These don't apply to Kubernetes, as those settings are configured via helm.

Append any of the following keys to your `.env` file, and run `docker-compose up -d` to apply them.

## AUTHENTIK_LOG_LEVEL

Log level for the server and worker containers. Possible values: debug, info, warning, error
Defaults to `info`.

## AUTHENTIK_ERROR_REPORTING

- AUTHENTIK_ERROR_REPORTING__ENABLED

  Enable error reporting. Defaults to `false`.

  Error reports are sent to https://sentry.beryju.org, and are used for debugging and general feedback. Anonymous performance data is also sent.

- AUTHENTIK_ERROR_REPORTING__ENVIRONMENT

  Unique environment that is attached to your error reports, should be set to your email address for example. Defaults to `customer`.

- AUTHENTIK_ERROR_REPORTING__SEND_PII

  Whether or not to send personal data, like usernames. Defaults to `false`.

## AUTHENTIK_EMAIL

- AUTHENTIK_EMAIL__HOST

  Default: `localhost`

- AUTHENTIK_EMAIL__PORT

  Default: `25`

- AUTHENTIK_EMAIL__USERNAME

  Default: `""`

- AUTHENTIK_EMAIL__PASSWORD

  Default: `""`

- AUTHENTIK_EMAIL__USE_TLS

  Default: `false`

- AUTHENTIK_EMAIL__USE_SSL

  Default: `false`

- AUTHENTIK_EMAIL__TIMEOUT

  Default: `10`

- AUTHENTIK_EMAIL__FROM

  Default: `authentik@localhost`

  Email address authentik will send from, should have a correct @domain

## AUTHENTIK_OUTPOSTS

- AUTHENTIK_OUTPOSTS__DOCKER_IMAGE_BASE

  This is the prefix used for authentik-managed outposts. Default: `beryju/authentik`.

## AUTHENTIK_AUTHENTIK

- AUTHENTIK_AUTHENTIK__AVATARS

  Controls which avatars are shown. Defaults to `gravatar`. Can be set to `none` to disable avatars.

- AUTHENTIK_AUTHENTIK__BRANDING__TITLE

  Branding title used throughout the UI. Defaults to `authentik`.

- AUTHENTIK_AUTHENTIK__BRANDING__LOGO

  Logo shown in the sidebar and flow executions. Defaults to `/static/dist/assets/icons/icon_left_brand.svg`
