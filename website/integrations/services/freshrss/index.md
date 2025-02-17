---
title: Integrate with FreshRSS
sidebar_label: FreshRSS
support_level: community
---

## What is FreshRSS

> FreshRSS is a self-hosted RSS feed aggregator.
>
> -- https://github.com/FreshRSS/FreshRSS

## Preparation

The following placeholders are used in this guide:

- `freshrss.company` is the FQDN of the FreshRSS installation.
- `port` is the port on which the FreshRSS install is running (usually 443)
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of FreshRss with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can create only an application, without a provider, by clicking **Create.)**

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Add two `Strict` redirect URI and set them to <kbd>https://<em>freshrss.company</em>/i/oidc/</kbd> and <kbd>https://<em>freshrss.company:443</em>/i/oidc/</kbd>. If FreshRSS is exposed on a port other than `443`, update the second redirect URI accordingly.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## FreshRSS configuration

:::info
This integration only works with the Docker or Kubernetes install of FreshRSS, using [FreshRSS docker image](https://hub.docker.com/r/freshrss/freshrss/), on x86_64 systems and without the Alpine version of the image. More information can be found on [this issue on FreshRSS GitHub](https://github.com/FreshRSS/FreshRSS/issues/5722)
:::

Add those environment variables to your _Docker_ image :

- `OIDC_ENABLED` : `1`
- `OIDC_PROVIDER_METADATA_URL` : `https://authentik.company/application/o/<application-slug>/.well-known/openid-configuration` replacing `<application-slug>` with the slug of your created application
- `OIDC_CLIENT_ID` : the client ID of your provider
- `OIDC_CLIENT_SECRET` : the client secret of your provider
- `OIDC_X_FORWARDED_HEADERS` : `X-Forwarded-Port X-Forwarded-Proto X-Forwarded-Host`
- `OIDC_SCOPES` : `openid email profile`

Before restarting your Docker container, ensure that one of the Admin users of your FreshRSS instance has the same login as one of your Authentik user.

Restart your FreshRSS container, and login as a user that exists on both FreshRSS and your Authentik.
Navigate to _Settings_ > _Authentication_ in your FreshRSS instance, and choose as an authentication method _HTTP (for advanced users with HTTPS)_

You can find additional information on [FreshRSS documentation](https://freshrss.github.io/FreshRSS/en/admins/16_OpenID-Connect.html)
