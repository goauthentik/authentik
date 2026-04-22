---
title: Kubernetes installation
---

You can install authentik to run on Kubernetes using a Helm chart.

:::info
You can also [view a video walk-through](https://www.youtube.com/watch?v=O1qUbrk4Yc8) of the installation process on Kubernetes (with bonus details about email configuration and other important options).
:::

## Requirements

- Kubernetes
- Helm

## Video

View our video about installing authentik on Kubernetes.

<iframe width="560" height="315" src="https://www.youtube.com/embed/O1qUbrk4Yc8?si=hs-ZhbVk4Y-TW_Vw&amp;start=562" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

## Generate passwords

Start by generating passwords for the database and cache. You can use either of the following commands:

```shell
pwgen -s 50 1
openssl rand 60 | base64 -w 0
```

## Set values

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
```

If your cluster or controller supports the Gateway API, replace the `server.ingress` section above with this Gateway API configuration:

```yaml
server:
    route:
        main:
            enabled: true
            hostnames:
                - authentik.domain.tld
            parentRefs:
                - name: shared-gateway
                  namespace: default
```

The Helm chart creates an `HTTPRoute`, but it does not create `Gateway` or `GatewayClass` resources. Create the `Gateway` separately, then set `server.route.main.parentRefs` to that `Gateway` resource's name and namespace. In the example above, `name: shared-gateway` and `namespace: default` must match the manually created `Gateway`.

If your cluster or controller does not support the Gateway API, use the `server.ingress` configuration shown above.

See all configurable values on [ArtifactHub](https://artifacthub.io/packages/helm/goauthentik/authentik).

## PostgreSQL production setup

The PostgreSQL database installed by default with the Helm chart is intended for demonstration and test environments.

For production deployments, use a separately managed PostgreSQL installation instead of relying on the chart's bundled database.

Common options include:

- [CloudNativePG](https://github.com/cloudnative-pg/cloudnative-pg)
- [Zalando Postgres Operator](https://github.com/zalando/postgres-operator)

After you provision PostgreSQL externally, configure authentik to use it with the settings in the [PostgreSQL configuration reference](../configuration/configuration.mdx#postgresql-settings).

## Email configuration (optional but recommended)

It is also recommended to configure global email settings. These are used by authentik to notify administrators about alerts, configuration issues and new releases. They can also be used by [Email stages](../../add-secure-apps/flows-stages/stages/email/index.mdx) to send verification/recovery emails.

For more information, refer to our [Email configuration](../email.mdx) documentation.

## Install authentik Helm Chart

Now, execute the following commands to install authentik:

```shell
helm repo add authentik https://charts.goauthentik.io
helm repo update
helm upgrade --install authentik authentik/authentik -f values.yaml
```

During the installation process, the database migrations will be applied automatically on startup.

## Access authentik

To start the initial setup, navigate to `http://<your server's IP or hostname>:9000`.

You are then prompted to set a password for the `akadmin` user (the default user).

:::info Issues with initial setup
If you run into issues, refer to our [troubleshooting docs](../../troubleshooting/login.md#cant-access-initial-setup-flow-during-installation-steps).
:::

## First steps in authentik

import BlurbFirstSteps from "../first-steps/\_blurb_first_steps.mdx";

<BlurbFirstSteps />
