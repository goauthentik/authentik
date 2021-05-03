---
title: Next
---

## Headline Changes

- Compatibility with forwardAuth/auth_request

    The authentik proxy is now compatible with forwardAuth (traefik) / auth_request (nginx). All that is required is the latest version of the outpost,
    and the correct config from [here](../outposts/proxy.mdx).

- Docker images for ARM

    Docker images are now built for amd64, arm64, arm v7 and arm v8.

- Deprecated Group membership has been removed.

## Minor changes

- Improved compatibility of the flow interface with password managers.

## Upgrading

This release does not introduce any new requirements.

### docker-compose

Download the latest docker-compose file from [here](https://raw.githubusercontent.com/goauthentik/authentik/version-2021.4/docker-compose.yml). Afterwards, simply run `docker-compose up -d` and then the standard upgrade command of `docker-compose run --rm server migrate`.

### Kubernetes

Run `helm repo update` and then upgrade your release with `helm upgrade authentik authentik/authentik --devel -f values.yaml`.
