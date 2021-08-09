---
title: Configuration
---

These are all the configuration options you can set via environment variables.

Append any of the following keys to your `.env` file, and run `docker-compose up -d` to apply them.

:::info
The double-underscores are intentional, as all these settings are translated to yaml internally, a double-underscore indicates the next level.
:::

All of these variables can be set to values, but you can also use a URI-like format to load values from other places:

- `env://<name>` Loads the value from the environment variable `<name>`. Fallback can be optionally set like `env://<name>?<default>`
- `file://<name>` Loads the value from the file `<name>`. Fallback can be optionally set like `file://<name>?<default>`

## PostgreSQL Settings

- `AUTHENTIK_POSTGRESQL__HOST`: Hostname of your PostgreSQL Server
- `AUTHENTIK_POSTGRESQL__NAME`: Database name
- `AUTHENTIK_POSTGRESQL__USER`: Database user
- `AUTHENTIK_POSTGRESQL__PASSWORD`: Database password, defaults to the environment variable `POSTGRES_PASSWORD`

## Redis Settings

- `AUTHENTIK_REDIS__HOST`: Hostname of your Redis Server
- `AUTHENTIK_REDIS__PASSWORD`: Password for your Redis Server
- `AUTHENTIK_REDIS__CACHE_DB`: Database for caching, defaults to 0
- `AUTHENTIK_REDIS__MESSAGE_QUEUE_DB`: Database for the message queue, defaults to 1
- `AUTHENTIK_REDIS__WS_DB`: Database for websocket connections, defaults to 2
- `AUTHENTIK_REDIS__OUTPOST_SESSION_DB`: Database for sessions for the embedded outpost, defaults to 3
- `AUTHENTIK_REDIS__CACHE_TIMEOUT`: Timeout for cached data until it expires in seconds, defaults to 300
- `AUTHENTIK_REDIS__CACHE_TIMEOUT_FLOWS`: Timeout for cached flow plans until they expire in seconds, defaults to 300
- `AUTHENTIK_REDIS__CACHE_TIMEOUT_POLICIES`: Timeout for cached polices until they expire in seconds, defaults to 300
- `AUTHENTIK_REDIS__CACHE_TIMEOUT_REPUTATION`: Timeout for cached reputation until they expire in seconds, defaults to 300

## authentik Settings

### AUTHENTIK_LOG_LEVEL

Log level for the server and worker containers. Possible values: debug, info, warning, error
Defaults to `info`.

### AUTHENTIK_ERROR_REPORTING

- `AUTHENTIK_ERROR_REPORTING__ENABLED`

  Enable error reporting. Defaults to `false`.

  Error reports are sent to https://sentry.beryju.org, and are used for debugging and general feedback. Anonymous performance data is also sent.

- `AUTHENTIK_ERROR_REPORTING__ENVIRONMENT`

  Unique environment that is attached to your error reports, should be set to your email address for example. Defaults to `customer`.

- `AUTHENTIK_ERROR_REPORTING__SEND_PII`

  Whether or not to send personal data, like usernames. Defaults to `false`.

### AUTHENTIK_EMAIL

- `AUTHENTIK_EMAIL__HOST`

  Default: `localhost`

- `AUTHENTIK_EMAIL__PORT`

  Default: `25`

- `AUTHENTIK_EMAIL__USERNAME`

  Default: `""`

- `AUTHENTIK_EMAIL__PASSWORD`

  Default: `""`

- `AUTHENTIK_EMAIL__USE_TLS`

  Default: `false`

- `AUTHENTIK_EMAIL__USE_SSL`

  Default: `false`

- `AUTHENTIK_EMAIL__TIMEOUT`

  Default: `10`

- `AUTHENTIK_EMAIL__FROM`

  Default: `authentik@localhost`

  Email address authentik will send from, should have a correct @domain

### AUTHENTIK_OUTPOSTS

- `AUTHENTIK_OUTPOSTS__DOCKER_IMAGE_BASE`

  Placeholders:
   - `%(type)s`: Outpost type; proxy, ldap, etc
   - `%(version)s`: Current version; 2021.4.1
   - `%(build_hash)s`: Build hash if you're running a beta version

  Placeholder for outpost docker images. Default: `ghcr.io/goauthentik/%(type)s:%(version)s`.

### AUTHENTIK_AVATARS

Configure how authentik should show avatars for users. Following values can be set:

- `none`: Disables per-user avatars and just shows a 1x1 pixel transparent picture
- `gravatar`: Uses gravatar with the user's email address
- Any URL: If you want to use images hosted on another server, you can set any URL.

  Additionally, these placeholders can be used:

   - `%(username)s`: The user's username
   - `%(mail_hash)s`: The email address, md5 hashed
   - `%(upn)s`: The user's UPN, if set (otherwise an empty string)
