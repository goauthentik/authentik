---
title: Next
---

## Headline Changes

- Duo two-factor support

    You can now add the new `authenticator_duo` stage to configure Duo authenticators. Duo has also been added as device class to the `authenticator_validation` stage.

    Currently, only Duo push notifications are supported. Because no additional input is required, Duo also works with the LDAP Outpost.

## Minor changes

- You can now specify which sources should be shown on an Identification stage.

## Upgrading

This release does not introduce any new requirements.

### docker-compose

Download the docker-compose file for 2021.6 from [here](https://raw.githubusercontent.com/goauthentik/authentik/version-2021.6/docker-compose.yml). Afterwards, simply run `docker-compose up -d`.

### Kubernetes

Upgrade to the latest chart version to get the new images.
