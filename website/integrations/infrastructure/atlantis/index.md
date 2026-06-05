---
title: Integrate with Atlantis
sidebar_label: Atlantis
support_level: community
---

## What is Atlantis?

> Atlantis is an application for automating Terraform via pull requests.
>
> -- https://www.runatlantis.io/guide

Atlantis does not provide native SSO for the web UI. Use authentik as a forward auth proxy in front of Atlantis, and allow the Atlantis webhook endpoint to remain reachable by your Git host.

## Preparation

The following placeholders are used in this guide:

- `atlantis.company` is the FQDN of the Atlantis installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Atlantis with authentik, you need to create an application/provider pair in authentik. This guide assumes that Atlantis is already deployed behind a reverse proxy that supports authentik forward auth.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **Proxy Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set **Mode** to **Forward auth (single application)**.
        - Set **External host** to `https://atlantis.company`.
        - Under **Advanced protocol settings**, set **Unauthenticated Paths** to the following value:

            ```text
            ^/events$
            ```

        - Under **Authentication settings**, disable **Intercept header authentication**.

    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

### Configure proxy outpost

The proxy provider requires an authentik proxy outpost. If you do not already have a proxy outpost, follow the [outpost documentation](/docs/add-secure-apps/outposts/) to create and deploy one.

Add the Atlantis application to the proxy outpost that should serve it:

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Outposts**.
3. Click the edit icon for the proxy outpost. This can be the built-in **authentik Embedded Outpost** or another proxy outpost.
4. Under **Available Applications**, select the Atlantis application and move it to **Selected Applications**.
5. Click **Update** to save your changes.

## Atlantis configuration

No SSO configuration is required in Atlantis.

Configure your reverse proxy to use the authentik outpost as the forward auth endpoint for `https://atlantis.company`.

Requests to `/outpost.goauthentik.io` must be routed to the authentik outpost. All other requests, including `/events`, must continue to be routed to Atlantis.

Configure your Git host webhook URL to `https://atlantis.company/events`. The `/events` endpoint is skipped by authentik so that Git host webhooks can reach Atlantis. Atlantis should still validate those webhook requests with its existing webhook secret or webhook authentication settings.

## Configuration verification

To verify the login flow, open Atlantis. You should be redirected to authentik before the Atlantis web interface is shown.

## Resources

- [Atlantis Docs - Introduction](https://www.runatlantis.io/guide)
- [Atlantis Docs - Configuring Webhooks](https://www.runatlantis.io/docs/configuring-webhooks.html)
- [Atlantis Docs - Webhook Secrets](https://www.runatlantis.io/docs/webhook-secrets)
- [Atlantis Docs - Deployment](https://www.runatlantis.io/docs/deployment.html)
