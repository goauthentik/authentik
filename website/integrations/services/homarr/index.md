---
title: Integrate with Homarr
sidebar_label: Homarr
support_level: community
---

## What is Homarr

> A sleek, modern dashboard that puts all of your apps and services at your fingertips. Control everything in one convenient location. Seamlessly integrates with the apps you've added, providing you with valuable information.
>
> -- https://homarr.dev/

## Preparation

The following placeholders are used in this guide:

- `homarr.company` is the FQDN of the Homarr installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Homarr with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Create two `strict` redirect URIs and set to `https://homarr.company/api/auth/callback/oidc` and ` http://localhost:50575/api/auth/callback/oidc`.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Homarr configuration

Add the following environment variables to your Homarr configuration. Make sure to fill in the Client ID, Client Secret, OIDC Issuer, and OIDC URI from your authentik instance.

```sh
AUTH_PROVIDERS="oidc,credentials"
AUTH_OIDC_CLIENT_ID=<Client ID from authentik>
AUTH_OIDC_CLIENT_SECRET=<Client secret from authentik>
AUTH_OIDC_ISSUER=https://authentik.company/application/o/<application_slug>/
AUTH_OIDC_URI=https://authentik.company/application/o/authorize
AUTH_OIDC_CLIENT_NAME=authentik
OAUTH_ALLOW_DANGEROUS_EMAIL_ACCOUNT_LINKING=true
# Optional: You can add this if you only want to allow auto login via authentik
# AUTH_OIDC_AUTO_LOGIN=true
```

Restart the Homarr service for the changes to take effect.
