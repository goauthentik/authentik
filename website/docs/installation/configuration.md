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
- `AUTHENTIK_POSTGRESQL__PORT`: Database port, defaults to 5432
- `AUTHENTIK_POSTGRESQL__PASSWORD`: Database password, defaults to the environment variable `POSTGRES_PASSWORD`

### PostgreSQL Backup Settings

- `AUTHENTIK_POSTGRESQL__BACKUP__ENABLED`: Controls if the inbuilt backup-mechanism is enabled, defaults to true (new in 2021.10).

Optionally enable automated database backups to S3 or S3-compatible storages.

- `AUTHENTIK_POSTGRESQL__S3_BACKUP__ACCESS_KEY`: S3 Access Key
- `AUTHENTIK_POSTGRESQL__S3_BACKUP__SECRET_KEY`: S3 Secret Key
- `AUTHENTIK_POSTGRESQL__S3_BACKUP__BUCKET`: S3 Bucket
- `AUTHENTIK_POSTGRESQL__S3_BACKUP__REGION`: S3 Region, defaults to `eu-central-1`
- `AUTHENTIK_POSTGRESQL__S3_BACKUP__LOCATION`: Relative Location of the files to the bucket. Defaults to the root of the bucket.

To use an S3-compatible storage, set the following settings.

- `AUTHENTIK_POSTGRESQL__S3_BACKUP__HOST`: URL to the Service, for example `https://play.min.io`
- `AUTHENTIK_POSTGRESQL__S3_BACKUP__INSECURE_SKIP_VERIFY`: Set to `true` to disable SSL Certificate verification.

## Redis Settings

- `AUTHENTIK_REDIS__HOST`: Hostname of your Redis Server
- `AUTHENTIK_REDIS__PASSWORD`: Password for your Redis Server
- `AUTHENTIK_REDIS__CACHE_DB`: Database for caching, defaults to 0
- `AUTHENTIK_REDIS__MESSAGE_QUEUE_DB`: Database for the message queue, defaults to 1
- `AUTHENTIK_REDIS__WS_DB`: Database for websocket connections, defaults to 2
- `AUTHENTIK_REDIS__OUTPOST_SESSION_DB`: Database for sessions for the embedded outpost, defaults to 3
- `AUTHENTIK_REDIS__CACHE_TIMEOUT`: Timeout for cached data until it expires in seconds, defaults to 300
- `AUTHENTIK_REDIS__CACHE_TIMEOUT_FLOWS`: Timeout for cached flow plans until they expire in seconds, defaults to 300
- `AUTHENTIK_REDIS__CACHE_TIMEOUT_POLICIES`: Timeout for cached policies until they expire in seconds, defaults to 300
- `AUTHENTIK_REDIS__CACHE_TIMEOUT_REPUTATION`: Timeout for cached reputation until they expire in seconds, defaults to 300

## authentik Settings

### AUTHENTIK_SECRET_KEY

Secret key used for cookie signing and unique user IDs, don't change this after the first install.

### AUTHENTIK_LOG_LEVEL

Log level for the server and worker containers. Possible values: debug, info, warning, error
Defaults to `info`.

### AUTHENTIK_COOKIE_DOMAIN

Which domain the session cookie should be set to. By default, the cookie is set to the domain authentik is accessed under.

### AUTHENTIK_DISABLE_UPDATE_CHECK

Disable the inbuilt update-checker. Defaults to `false`.

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

- `AUTHENTIK_OUTPOSTS__CONTAINER_IMAGE_BASE`

  Placeholders:
   - `%(type)s`: Outpost type; proxy, ldap, etc
   - `%(version)s`: Current version; 2021.4.1
   - `%(build_hash)s`: Build hash if you're running a beta version

  Placeholder for outpost docker images. Default: `goauthentik.io/%(type)s:%(version)s`.

### AUTHENTIK_AVATARS

Configure how authentik should show avatars for users. Following values can be set:

- `none`: Disables per-user avatars and just shows a 1x1 pixel transparent picture
- `gravatar`: Uses gravatar with the user's email address (default)
- Any URL: If you want to use images hosted on another server, you can set any URL.

  Additionally, these placeholders can be used:

   - `%(username)s`: The user's username
   - `%(mail_hash)s`: The email address, md5 hashed
   - `%(upn)s`: The user's UPN, if set (otherwise an empty string)

### AUTHENTIK_DEFAULT_USER_CHANGE_EMAIL

:::info
Requires authentik 2021.10.5
:::

Enable the ability for users to change their Email address, defaults to `true`.

### AUTHENTIK_DEFAULT_USER_CHANGE_USERNAME

:::info
Requires authentik 2021.10.5
:::

Enable the ability for users to change their Usernames, defaults to `true`.

### AUTHENTIK_FOOTER_LINKS

:::info
Requires authentik 2021.10.5
:::

This option configures the footer links on the flow executor pages.

The setting can be used as follows:

```
AUTHENTIK_FOOTER_LINKS='[{"name": "Link Name","href":"https://goauthentik.io"}]'
```

## Debugging

To check if your config has been applied correctly, you can run the following command to output the full config:

```
docker-compose run --rm worker dump_config
# Or for kubernetes
kubectl exec -it deployment/authentik-worker -c authentik -- ak dump_config
```
