---
title: Release next
slug: /releases/next
---
<!-- ## Breaking changes -->

## Breaking changes

### Manual action is required

### Manual action may be required

-   **Configuration options migrated to the Admin interface**

    The following config options have been moved from the config file and can now be set using the Admin interface (under **System** -> **Settings**) or the API:

    -   `AUTHENTIK_DEFAULT_TOKEN_LENGTH`

    When upgrading to 2024.next, the currently configured options will be automatically migrated to the database, and can be removed from the `.env` or helm values file afterwards.

## New features

-   Configurable app password token expiring

    Thanks @jmdilly for contributing this feature!

    Admins can now configure the default token duration (which defaults to `minutes=30`) in the admin interface as specified above. This value can also be overridden per-user with the `goauthentik.io/user/token-maximum-lifetime` attribute.

## Upgrading

This release does not introduce any new requirements.

### docker-compose

To upgrade, download the new docker-compose file and update the Docker stack with the new version, using these commands:

```
wget -O docker-compose.yml https://goauthentik.io/version/xxxx.x/docker-compose.yml
docker compose up -d
```

The `-O` flag retains the downloaded file's name, overwriting any existing local file with the same name.

### Kubernetes

Upgrade the Helm Chart to the new version, using the following commands:

```shell
helm repo update
helm upgrade authentik authentik/authentik -f values.yaml --version ^xxxx.x
```

## Minor changes/fixes

<!-- _Insert the output of `make gen-changelog` here_ -->

## API Changes

<!-- _Insert output of `make gen-diff` here_ -->
