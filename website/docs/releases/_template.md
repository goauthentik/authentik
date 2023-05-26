---
title: Release xxxx.x
slug: "/releases/xxxx.x"
---

## Breaking changes

## New features

## Upgrading

This release does not introduce any new requirements.

### docker-compose

Download the docker-compose file for xxxx.x from [here](https://goauthentik.io/version/xxxx.x/docker-compose.yml). Afterwards, run `docker-compose up -d`.

:::info
To download the latest `docker-compose.yml` file you can use the `wget` command followed by the file's location URL.

Example: `wget -O docker-compose.yml https://goauthentik.io/docker-compose.yml`
:::

### Kubernetes

Update your values to use the new images:

```yaml
image:
    repository: ghcr.io/goauthentik/server
    tag: xxxx.x.0
```

## Minor changes/fixes

_Insert the output of `make gen-changelog` here_

## API Changes

_Insert output of `make gen-diff` here_
