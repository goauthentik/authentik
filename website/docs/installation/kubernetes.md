---
title: Kubernetes installation
---

authentik is installed using a helm-chart.

To install authentik using the helm chart, generate a password for the database and the cache, using `pwgen -s 50 1` or `openssl rand -base64 36`.

Create a values.yaml file with a minimum of these settings:

```yaml
authentik:
    secret_key: "PleaseGenerateA50CharKey"
    # This sends anonymous usage-data, stack traces on errors and
    # performance data to sentry.io, and is fully opt-in
    error_reporting:
        enabled: true
    postgresql:
        password: "ThisIsNotASecurePassword"

ingress:
    enabled: true
    hosts:
        - host: authentik.domain.tld
          paths:
              - path: "/"
                pathType: Prefix

postgresql:
    enabled: true
    postgresqlPassword: "ThisIsNotASecurePassword"
redis:
    enabled: true
```

See all configurable values on [artifacthub](https://artifacthub.io/packages/helm/goauthentik/authentik).

Afterwards, run these commands to install authentik:

```
helm repo add authentik https://charts.goauthentik.io
helm repo update
helm upgrade --install authentik authentik/authentik -f values.yaml
```

This installation automatically applies database migrations on startup. After the installation is done, navigate to the `https://<ingress you've specified>/if/flow/initial-setup/`, to set a password for the akadmin user.

It is also recommended to configure global email credentials. These are used by authentik to notify you about alerts, configuration issues. They can also be used by [Email stages](../flow/stages/email/) to send verification/recovery emails.
