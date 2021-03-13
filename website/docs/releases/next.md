---
title: Next
---

# TBD

## Upgrading

This release does not introduce any new requirements.

### docker-compose

Download the latest docker-compose file from [here](https://raw.githubusercontent.com/BeryJu/authentik/version-2021.4/docker-compose.yml). Afterwards, simply run `docker-compose up -d` and then the standard upgrade command of `docker-compose run --rm server migrate`.

### Kubernetes

Run `helm repo update` and then upgrade your release with `helm upgrade passbook authentik/authentik --devel -f values.yaml`.
