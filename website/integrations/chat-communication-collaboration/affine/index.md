---
title: Integrate with AFFiNE
sidebar_label: AFFiNE
support_level: community
---

## What is AFFiNE

> AFFiNE is an open-source platform that allows you to bring together documents, whiteboards, and databases. It is a reliable tool designed to create a professional workspace for your work. With AFFiNE, you can focus on practicality and efficiency, making it easier to collaborate on your projects.
>
> -- https://affine.pro/

## Preparation

The following placeholders are used in this guide:

- `affine.company` is the FQDN of the AFFiNE installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of AFFiNE with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
    - Create a `Strict` redirect URI and set to `https://affine.company/oauth/callback`.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## AFFiNE configuration

1. Log in to AFFiNE as an administrator.
2. Navigate to the Admin Panel of your instance by clicking on your profile picture.
3. Navigate to **Settings** > **OAuth**.
4. Under **OIDC OAuth provider config**, set the following JSON data:

```json
{
    "args": {},
    "issuer": "https://authentik.company/application/o/<application_slug>/",
    "clientId": "<Client ID from authentik>",
    "clientSecret": "<Client Secret from authentik>"
}
```

4. Save the changes.

## Configuration verification

To verify the integration of authentik with AFFiNE, log out of AFFiNE, then on the login page click on **Continue with OIDC**. You should be redirected to authentik, and once authenticated, logged in to AFFiNE.

## Resources

- [AFFiNE Docs - OAuth 2.0 ](https://docs.affine.pro/self-host-affine/administer/oauth-2-0#oidc)
