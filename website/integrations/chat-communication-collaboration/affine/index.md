---
title: Integrate with AFFiNE
sidebar_label: AFFiNE
support_level: community
---

## What is AFFiNE?

> AFFiNE is an open-source, self-hostable workspace for documents, whiteboards, and databases.
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
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
        - Add one `Strict` redirect URI and set it to `https://affine.company/oauth/callback`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## AFFiNE configuration

1. Log in to AFFiNE as an administrator.
2. Click your profile picture and navigate to **Admin Panel** > **Settings** > **OAuth**.
3. Under **OIDC OAuth provider config**, set the following JSON data:

```json
{
    "args": {},
    "issuer": "https://authentik.company/application/o/<application_slug>",
    "clientId": "<Client ID from authentik>",
    "clientSecret": "<Client Secret from authentik>"
}
```

4. Save the changes.

## Configuration verification

To confirm that authentik is properly configured with AFFiNE, open AFFiNE and log in using the **Continue with OIDC** login option. You should be redirected to authentik for authentication and then redirected back to AFFiNE.

## Resources

- [AFFiNE OAuth 2.0 documentation](https://docs.affine.pro/self-host-affine/administer/oauth-2-0#oidc)
- [AFFiNE OIDC provider source](https://github.com/toeverything/AFFiNE/blob/canary/packages/backend/server/src/plugins/oauth/providers/oidc.ts)
