---
title: Integrate with PhotoPrism
sidebar_label: PhotoPrism
support_level: community
---

## What is PhotoPrism?

> PhotoPrism is an AI-powered photos app that lets you browse, organize, and find photos and videos on a home server, private server, or in the cloud.
>
> -- https://www.photoprism.app/

## Preparation

The following placeholders are used in this guide:

- `photoprism.company` is the FQDN of the PhotoPrism installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

:::warning HTTPS required
PhotoPrism requires HTTPS for OpenID Connect (OIDC). Make sure that the `PHOTOPRISM_SITE_URL` value, the PhotoPrism redirect URI in authentik, and the public URL users use to access PhotoPrism all use the same HTTPS hostname.
:::

## authentik configuration

To support the integration of PhotoPrism with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add one `Strict` redirect URI and set it to `https://photoprism.company/api/v1/oidc/redirect`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## PhotoPrism configuration

Configure PhotoPrism with the OIDC settings from authentik. Add the following settings to your PhotoPrism `.env` file:

```text title=".env"
PHOTOPRISM_SITE_URL=https://photoprism.company/
PHOTOPRISM_OIDC_URI=https://authentik.company/application/o/<application_slug>/
PHOTOPRISM_OIDC_CLIENT=<Client ID from authentik>
PHOTOPRISM_OIDC_SECRET=<Client Secret from authentik>
PHOTOPRISM_OIDC_SCOPES=openid email profile
PHOTOPRISM_OIDC_PROVIDER=authentik
# Optional: Automatically redirect unauthenticated users to authentik.
PHOTOPRISM_OIDC_REDIRECT=false
# Optional: Allow PhotoPrism to create new accounts from OIDC logins.
PHOTOPRISM_OIDC_REGISTER=true
```

Restart PhotoPrism after changing these settings.

## Configuration verification

To confirm that authentik is properly configured with PhotoPrism, log out of PhotoPrism and log back in using the **authentik** OIDC login option. You should be redirected to authentik for authentication and then redirected back to PhotoPrism.

## Resources

- [PhotoPrism OpenID Connect documentation](https://docs.photoprism.app/getting-started/advanced/openid-connect/)
- [PhotoPrism Config Options documentation](https://docs.photoprism.app/getting-started/config-options/)
