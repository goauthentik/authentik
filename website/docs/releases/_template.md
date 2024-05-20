---
title: Release xxxx.x
slug: "/releases/xxxx.x"
---

:::::note
xxxx.x has not been released yet! We're publishing these release notes as a preview of what's to come, and for our awesome beta testers trying out release candidates.

To try out the release candidate, replace your Docker image tag with the latest release candidate number, such as xxxx.x.0-rc1. You can find the latest one in [the latest releases on GitHub](https://github.com/goauthentik/authentik/releases). If you don't find any, it means we haven't released one yet.
:::::

<!-- ## Breaking changes -->

## New features

## Upgrading

This release does not introduce any new requirements.

### docker-compose

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
