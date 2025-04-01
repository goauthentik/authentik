---
title: Integrate with Hoarder
sidebar_label: Hoarder
support_level: community
---

## What is Hoarder

> A self-hostable bookmark-everything app (links, notes and images) with AI-based automatic tagging and full-text search.
>
> -- https://hoarder.app/

## Preparation

The following placeholders are used in this guide:

- `hoarder.company` is the FQDN of the Hoarder installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Hoarder with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can create only an application, without a provider, by clicking **Create**.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to <kbd>https://<em>hoarder.company</em>/api/auth/callback/custom</kbd>.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Hoarder configuration

In Hoarder, you'll need to add these environment variables:

```sh
NEXTAUTH_URL=https://hoarder.company
OAUTH_CLIENT_ID=<Client ID from authentik>
OAUTH_CLIENT_SECRET=<Client secret from authentik>
OAUTH_WELLKNOWN_URL=https://authentik.company/application/o/hoarder/.well-known/openid-configuration
OAUTH_PROVIDER_NAME=authentik
OAUTH_ALLOW_DANGEROUS_EMAIL_ACCOUNT_LINKING=true
# Optional: You can add this if you only want to allow login with Authentik
# DISABLE_PASSWORD_AUTH=true
# Optional but highly recommended:
# DISABLE_SIGNUPS=true
```

Finally, restart the Hoarder server and test your configuration.
