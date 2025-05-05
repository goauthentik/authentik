---
title: Integrate with Coder
sidebar_label: Coder
support_level: community
---

## What is Coder

> Coder is an open-source platform that provides browser-based cloud development environments, enabling developers and teams to securely write, edit, and manage code remotely without the need for local setup
>
> -- https://coder.com

## Preparation

The following placeholders are used in this guide:

- `coder.company` is the FQDN of your Coder installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Coder with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to `https://coder.company/api/v2/users/oidc/callback`.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Coder configuration

To support the integration of Coder with authentik, update your `.env` file to include the following variables:

```yaml showLineNumbers title=".env"
CODER_OIDC_ISSUER_URL=https://authentik.company/application/o/<application slug>/
CODER_OIDC_EMAIL_DOMAIN=acme.company,acme-corp.company
CODER_OIDC_CLIENT_ID=<Client ID from authentik>
CODER_OIDC_CLIENT_SECRET=<Client secret from authentik>
CODER_OIDC_SIGN_IN_TEXT=Log in with authentik
CODER_OIDC_ICON_URL=https://authentik.company/static/dist/assets/icons/icon.png
```

## Resources

- [Coder OIDC authentication documentatiom](https://coder.com/docs/admin/users/oidc-auth/)

## Configuration verification

To confirm that authentik is properly configured with Coder, log out and attempt to log back in by clicking **Log in with authentik**.
