---
title: Integrate with Paperless-ng
sidebar_label: Paperless-ng
support_level: community
---

## What is Paperless-ng?

> Paperless-ng is an application that indexes scanned documents, makes them searchable, and stores document metadata. It was a fork of the original Paperless project and is no longer maintained.
>
> -- https://github.com/jonaswinkler/paperless-ng

Paperless-ng supports remote-user authentication through HTTP headers. This guide uses authentik as a forward auth proxy in front of Paperless-ng and configures Paperless-ng to trust the username header set by authentik.

## Preparation

The following placeholders are used in this guide:

- `paperless.company` is the FQDN of the Paperless-ng installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

:::warning Remote-user header authentication
Paperless-ng signs in users based on the trusted remote-user header. Configure your reverse proxy so that requests from clients cannot set or override the `X-Authentik-Username` header before the request reaches Paperless-ng.

Do not expose Paperless-ng directly to the internet when remote-user authentication is enabled.
:::

## authentik configuration

To support the integration of Paperless-ng with authentik, you need to create an application/provider pair in authentik. This guide assumes that Paperless-ng is already deployed behind a reverse proxy that supports authentik forward auth.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **Proxy Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set **Mode** to **Forward auth (single application)**.
        - Set **External host** to `https://paperless.company`.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

### Configure proxy outpost

The proxy provider requires an authentik proxy outpost. If you do not already have a proxy outpost, follow the [outpost documentation](/docs/add-secure-apps/outposts/) to create and deploy one.

Add the Paperless-ng application to a proxy outpost that will serve it:

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Outposts**.
3. Click the edit icon for the proxy outpost. This can be the built-in **authentik Embedded Outpost** or another proxy outpost.
4. Under **Available Applications**, select the Paperless-ng application and move it to **Selected Applications**.
5. Click **Update** to save your changes.

## Paperless-ng configuration

If you run Paperless-ng with Docker, add the following environment variables to `docker-compose.env`. For non-Docker installations, add the same values to `paperless.conf`.

```env title="docker-compose.env"
PAPERLESS_ENABLE_HTTP_REMOTE_USER=true
PAPERLESS_HTTP_REMOTE_USER_HEADER_NAME=HTTP_X_AUTHENTIK_USERNAME
PAPERLESS_LOGOUT_REDIRECT_URL=https://paperless.company/outpost.goauthentik.io/sign_out
```

To sign in to an existing Paperless-ng user, the authentik username must match the Paperless-ng username. If the username does not exist, Paperless-ng can create a separate user for the remote-user username.

Configure your reverse proxy to use the authentik outpost as the forward auth endpoint for `https://paperless.company`. Requests to `/outpost.goauthentik.io` must be routed to the authentik outpost, and all other requests must be routed to Paperless-ng.

After making these changes, restart Paperless-ng and reload your reverse proxy.

## Configuration verification

To verify the login flow, open Paperless-ng. You should be redirected to authentik before the Paperless-ng web interface is shown.

## Resources

- [Paperless-ng documentation - Configuration](https://paperless-ngx.readthedocs.io/en/ng-1.5.0/configuration.html)
