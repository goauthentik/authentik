---
title: Kubernetes installation
---

For a mid to high-load installation, Kubernetes is recommended. authentik is installed using a helm-chart.

To install authentik using the helm chart, generate a password for the database and the cache, using `pwgen` or `openssl rand -base64 36`.

Create a values.yaml file with a minimum of these settings:

```yaml
postgresql:
  postgresqlPassword: "<password you generated>"
redis:
  password: "<another password you generated>"
config:
  secretKey: "<another password you generated>"
```

See all configurable values on [artifacthub](https://artifacthub.io/packages/helm/goauthentik/authentik).

Afterwards, run these commands to install authentik:

```
helm repo add authentik https://helm.goauthentik.io
helm repo update
helm install authentik/authentik -f values.yaml
```

This installation automatically applies database migrations on startup. After the installation is done, navigate to the `https://<ingress you've specified>/if/flow/initial-setup/`, to set a password for the akadmin user.

It is also recommended to configure global email credentials. These are used by authentik to notify you about alerts, configuration issues. They can also be used by [Email stages](flow/stages/email/index.md) to send verification/recovery emails.
