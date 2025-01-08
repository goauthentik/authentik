---
title: Kubernetes installation
---

You can install authentik to run on Kubernetes using Helm Chart.

:::info
You can also [view a video walk-through](https://www.youtube.com/watch?v=O1qUbrk4Yc8) of the installation process on Kubernetes (with bonus details about email configuration and other important options).
:::

### Requirements

- Kubernetes
- Helm

## Video

<iframe width="560" height="315" src="https://www.youtube.com/embed/O1qUbrk4Yc8?si=hs-ZhbVk4Y-TW_Vw&amp;start=562" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

### Generate Passwords

Start by generating passwords for the database and cache. You can use either of the following commands:

```shell
pwgen -s 50 1
openssl rand 60 | base64 -w 0
```

### Set Values

Create a `values.yaml` file with a minimum of these settings:

```yaml
authentik:
    secret_key: "PleaseGenerateASecureKey"
    # This sends anonymous usage-data, stack traces on errors and
    # performance data to sentry.io, and is fully opt-in
    error_reporting:
        enabled: true
    postgresql:
        password: "ThisIsNotASecurePassword"

server:
    ingress:
        # Specify kubernetes ingress controller class name
        ingressClassName: nginx | traefik | kong
        enabled: true
        hosts:
            - authentik.domain.tld

postgresql:
    enabled: true
    auth:
        password: "ThisIsNotASecurePassword"
redis:
    enabled: true
```

See all configurable values on [ArtifactHub](https://artifacthub.io/packages/helm/goauthentik/authentik).

### Install authentik Helm Chart

Now, execute the following commands to install authentik:

```shell
helm repo add authentik https://charts.goauthentik.io
helm repo update
helm upgrade --install authentik authentik/authentik -f values.yaml
```

During the installation process, the database migrations will be applied automatically on startup.

### Accessing authentik

After the installation is complete, access authentik at `https://<ingress-host-name>/if/flow/initial-setup/`. Here, you can set a password for the default `akadmin` user.

:::info
User will get a `404 NOT FOUND` if initial setup URL doesn't include the trailing forward slash `/`. Make sure you use the complete url (`http://<your server's IP or hostname>:9000/if/flow/initial-setup/`) including the trailing forward slash.
:::

### Optional step: Configure global email credentials

It is recommended to configure global email credentials as well. These are used by authentik to notify you about alerts and configuration issues. Additionally, they can be utilized by [Email stages](../../add-secure-apps/flows-stages/stages/email/index.mdx) to send verification and recovery emails.

To configure this, append this block to your `values.yaml` file:

```yaml
# add this block under the `authentik:` block in your values.yaml file
# authentik:
email:
    # -- SMTP Server emails are sent from, fully optional
    host: ""
    port: 587
    # -- SMTP credentials. When left empty, no authentication will be done.
    username: ""
    # -- SMTP credentials. When left empty, no authentication will be done.
    password: ""
    # -- Enable either use_tls or use_ssl. They can't be enabled at the same time.
    use_tls: false
    # -- Enable either use_tls or use_ssl. They can't be enabled at the same time.
    use_ssl: false
    # -- Connection timeout in seconds
    timeout: 30
    # -- Email 'from' address can either be in the format "foo@bar.baz" or "authentik <foo@bar.baz>"
    from: ""
```

By following these steps, you will successfully install and set up authentik on Kubernetes using Helm.
