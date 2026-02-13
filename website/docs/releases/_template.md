---
title: Release xxxx.x
slug: "/releases/xxxx.x"
---

## Highlights

<!-- ## Breaking changes -->

## New features and improvements

## Upgrading

This release does not introduce any new requirements. You can follow the upgrade instructions below; for more detailed information about upgrading authentik, refer to our [Upgrade documentation](../install-config/upgrade.mdx).

:::warning
When you upgrade, be aware that the version of the authentik instance and of any outposts must be the same. We recommended that you always upgrade any outposts at the same time you upgrade your authentik instance.
:::

### Docker Compose

To upgrade, download the new docker-compose file and update the Docker stack with the new version, using these commands:

```shell
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
