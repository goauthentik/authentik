---
title: Release xxxx.x
slug: "/releases/xxxx.x"
---

<!-- ## Breaking changes -->

## New features

## Upgrading

This release does not introduce any new requirements.

### docker-compose

To upgrade, download the new docker-compose file and update the Docker stack with the new version, using these commands:

```
wget -O docker-compose.yml https://goauthentik.io/version/xxxx.x/docker-compose.yml
docker-compose up -d
```

The `-O` flag retains the downloaded file's name, overwriting any existing local file with the same name.

### Kubernetes

Update your values to use the new images:

```yaml
image:
    repository: ghcr.io/goauthentik/server
    tag: xxxx.x.0
```

## Minor changes/fixes

<!-- _Insert the output of `make gen-changelog` here_ -->

## API Changes

<!-- _Insert output of `make gen-diff` here_ -->
