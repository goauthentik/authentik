---
title: Integrate with Dozzle
sidebar_label: Dozzle
support_level: community
---

## What is Dozzle?

> Dozzle is a lightweight, web-based log viewer designed to simplify monitoring and debugging containerized applications across Docker, Docker Swarm, and Kubernetes environments.
>
> -- https://dozzle.dev/guide/what-is-dozzle

Dozzle supports forward-proxy authentication. Use authentik as a forward auth proxy in front of Dozzle, and configure Dozzle to read the authenticated user details from authentik's proxy headers.

## Preparation

The following placeholders are used in this guide:

- `dozzle.company` is the FQDN of the Dozzle installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

:::warning Protect Docker access
Dozzle can access the Docker API through the mounted Docker socket. Only expose Dozzle behind authentication, and keep Dozzle actions and shell access disabled unless you need them.
:::

## authentik configuration

To support the integration of Dozzle with authentik, you need to create an application/provider pair in authentik. This guide assumes that Dozzle is already deployed behind a reverse proxy that supports authentik forward auth.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **Proxy Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set **Mode** to **Forward auth (single application)**.
        - Set **External host** to `https://dozzle.company`.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

### Configure proxy outpost

The proxy provider requires an authentik proxy outpost. If you do not already have a proxy outpost, follow the [outpost documentation](/docs/add-secure-apps/outposts/) to create and deploy one.

Add the Dozzle application to a proxy outpost that will serve it:

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Outposts**.
3. Click the edit icon for the proxy outpost. This can be the built-in **authentik Embedded Outpost** or another proxy outpost.
4. Under **Available Applications**, select the Dozzle application and move it to **Selected Applications**.
5. Click **Update** to save your changes.

## Dozzle configuration

Configure Dozzle to use the `forward-proxy` authentication provider. Add the following environment variables to your Dozzle configuration:

```env title=".env"
DOZZLE_AUTH_PROVIDER=forward-proxy
DOZZLE_AUTH_HEADER_USER=X-Authentik-Username
DOZZLE_AUTH_HEADER_EMAIL=X-Authentik-Email
DOZZLE_AUTH_HEADER_NAME=X-Authentik-Name
DOZZLE_AUTH_LOGOUT_URL=https://dozzle.company/outpost.goauthentik.io/sign_out
```

Configure your reverse proxy to use the authentik outpost as the forward auth endpoint for `https://dozzle.company`. Requests to `/outpost.goauthentik.io` must be routed to the authentik outpost, and all other requests must be routed to Dozzle.

After making these changes, restart Dozzle and reload your reverse proxy.

## Configuration verification

To verify the login flow, open Dozzle. You should be redirected to authentik before the Dozzle web interface is shown.

## Resources

- [Dozzle - What is Dozzle?](https://dozzle.dev/guide/what-is-dozzle)
