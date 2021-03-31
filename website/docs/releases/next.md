---
title: Next
---

## Headline Changes

- Configurable Policy engine mode

    In the past, all objects, which could have policies attached to them, required *all* policies to pass to consider an action successful.
    You can now configure if *all* policies need to pass, or if *any* policy needs to pass.

    This can now be configured for the following objects:

        - Applications (access restrictions)
        - Sources
        - Flows
        - Flow-stage bindings

    For backwards compatibility, this is set to *all*, but new objects will default to *any*.

## Upgrading

This release does not introduce any new requirements.

### docker-compose

Download the latest docker-compose file from [here](https://raw.githubusercontent.com/BeryJu/authentik/version-2021.4/docker-compose.yml). Afterwards, simply run `docker-compose up -d` and then the standard upgrade command of `docker-compose run --rm server migrate`.

### Kubernetes

Run `helm repo update` and then upgrade your release with `helm upgrade passbook authentik/authentik --devel -f values.yaml`.
