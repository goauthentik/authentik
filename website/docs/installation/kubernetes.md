---
title: Kubernetes installation
---

You can install authentik to run on Kubernetes using Helm Chart

### Requirements

-   Kubernetes
-   Helm

### Generate Passwords
Start by generating passwords for the database and cache. You can use either of the following commands:

```
pwgen -s 50 1
openssl rand -base64 36
```

### Set Values

Create a `values.yaml` file with a minimum of these settings:

```yaml
authentik:
    secret_key: "PleaseGenerateA50CharKey"
    # This sends anonymous usage-data, stack traces on errors and
    # Performance data to sentry.io, and is fully opt-in
    error_reporting:
        enabled: true
    postgresql:
        password: "ThisIsNotASecurePassword"

ingress:
    # Specify kubernetes ingress controller class name
    ingressClassName: nginx | traefik | kong
    enabled: true
    hosts:
        # Specify external host name
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

### Install authentik Helm Chart

Now, execute the following commands to install authentik

```
helm repo add authentik https://charts.goauthentik.io
helm repo update
helm upgrade --install authentik authentik/authentik -f values.yaml
```

During the installation process, the database migrations will be applied automatically on startup.

### Accessing authentik
Once the installation is complete, access authentik at `https://<ingress-host-name>/if/flow/initial-setup/`. Here, you can set a password for the akadmin user.

### Optional Step: Configure Global Email Credentials
It is recommended to configure global email credentials as well. These are used by authentik to notify you about alerts and configuration issues. Additionally, they can be utilized by Email stages to send verification and recovery emails.

By following these steps, you will successfully install and set up authentik on Kubernetes using Helm.
