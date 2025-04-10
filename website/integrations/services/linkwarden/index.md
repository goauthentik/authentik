---
title: Integrate with Linkwarden
sidebar_label: Linkwarden
support_level: community
---

## What is Linkwarden

> Linkwarden is an open-source collaborative bookmark manager used to collect, organize, and preserve webpages.
>
> -- https://linkwarden.app/

## Preparation

The following placeholders are used in this guide:

- `linkwarden.company` is the FQDN of the Linkwarden installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Linkwarden with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to <kbd>https://<em>linkwarden.company</em>/api/v1/auth/callback/authentik</kbd>.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Linkwarden configuration

To configure Linkwarden to use authentik, add the following values to your `.env` file:

```
NEXT_PUBLIC_AUTHENTIK_ENABLED=true
AUTHENTIK_CUSTOM_NAME=authentik # Optionally set a custom provider name. Will be displayed on the login page
AUTHENTIK_ISSUER=https://authentik.company/application/o/<application slug>
AUTHENTIK_CLIENT_ID=<Your Client ID>
AUTHENTIK_CLIENT_SECRET=<Your Client Secret>
```

After making these changes, restart your Docker containers to apply the new configuration.

Once completed, Linkwarden should be successfully configured to use authentik as its Single Sign-On SSO provider.
