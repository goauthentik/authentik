---
title: Kubernetes installation
---

You can install authentik to run on Kubernetes using Helm Chart.

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
    # performance data to sentry.io, and is fully opt-in
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

See all configurable values on [ArtifactHub](https://artifacthub.io/packages/helm/goauthentik/authentik).

### Install authentik Helm Chart

Now, execute the following commands to install authentik

```
helm repo add authentik https://charts.goauthentik.io
helm repo update
helm upgrade --install authentik authentik/authentik -f values.yaml
```

During the installation process, the database migrations will be applied automatically on startup.

### Accessing authentik

Once the installation is complete, access authentik at `https://<ingress-host-name>/if/flow/initial-setup/`. Here, you can set a password for the default akadmin user.

### Optional step: Configure global email credentials

It is recommended to configure global email credentials as well. These are used by authentik to notify you about alerts and configuration issues. Additionally, they can be utilized by [Email stages](../flow/stages/email/index.mdx) to send verification and recovery emails.

To configure this, append this block to your `values.yaml` file:

```yaml
# add this block under the `authentik:` block in your values.yaml file
# authentik:
email:
    # -- SMTP Server emails are sent from, fully optional
    host: ""
    port: 587
    # -- SMTP credentials, when left empty, no authentication will be done
    username: ""
    # -- SMTP credentials, when left empty, no authentication will be done
    password: ""
    # -- Enable either use_tls or use_ssl, they can't be enabled at the same time.
    use_tls: false
    # -- Enable either use_tls or use_ssl, they can't be enabled at the same time.
    use_ssl: false
    # -- Connection timeout
    timeout: 30
    # -- Email from address, can either be in the format "foo@bar.baz" or "authentik <foo@bar.baz>"
    from: ""
```

By following these steps, you will successfully install and set up authentik on Kubernetes using Helm.
