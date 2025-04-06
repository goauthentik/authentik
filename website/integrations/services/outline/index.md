---
title: Integrate with Outline
sidebar_label: Outline
support_level: community
---

## What is Outline

> Your team's knowledge base.
> Lost in a mess of Docs? Never quite sure who has access? Colleagues requesting the same information repeatedly in chat? It’s time to get your team’s knowledge organized.
>
> -- https://www.getoutline.com

## Preparation

The following placeholders are used in this guide:

- `outline.company` is the FQDN of the Outline installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Outline with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to <kbd>https://<em>outline.company</em>/auth/oidc.callback</kbd>.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Outline configuration

You need to set the following `env` variables for Docker-based installations.

1. Set the following values:

```yaml
OIDC_CLIENT_ID=
OIDC_CLIENT_SECRET=
OIDC_AUTH_URI=https://authentik.company/application/o/authorize/
OIDC_TOKEN_URI=https://authentik.company/application/o/token/
OIDC_USERINFO_URI=https://authentik.company/application/o/userinfo/
OIDC_LOGOUT_URI=https://authentik.company/application/o/wiki/end-session/
OIDC_USERNAME_CLAIM=preferred_username
OIDC_DISPLAY_NAME=authentik
OIDC_SCOPES=openid profile email
```
