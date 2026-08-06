---
title: Integrate with Seerr
sidebar_label: Seerr
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Seerr?

> Seerr is a free, open-source request management and media discovery tool for Jellyfin, Plex, and Emby.
>
> -- https://seerr.dev/

## Preparation

The following placeholders are used in this guide:

- `seerr.company` is the FQDN of the Seerr installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Seerr with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **Slug** value as it will be required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add two **Redirect URIs**:
            - `Strict` `Authorization` `https://seerr.company/login`
            - `Strict` `Authorization` `https://seerr.company/profile/settings/linked-accounts`
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## Seerr configuration

:::warning Preview feature
Seerr OpenID Connect support is currently experimental. Use the `preview-new-oidc` Docker tag and back up your Seerr configuration before changing it.
:::

1. Stop Seerr.
2. Open your Seerr `settings.json` file. For Docker installations, this file is usually in the mounted `/app/config` directory.
3. Enable OpenID Connect sign-in and add authentik to the `oidc.providers` list. If you already have providers configured, add this object to the existing list.

```json title="settings.json (excerpt)"
{
    "main": {
        "oidcLogin": true
    },
    "oidc": {
        "providers": [
            {
                "slug": "authentik",
                "name": "authentik",
                "issuerUrl": "https://authentik.company/application/o/<application_slug>/",
                "clientId": "<Client ID from authentik>",
                "clientSecret": "<Client Secret from authentik>",
                "logo": "https://authentik.company/static/dist/assets/icons/icon.svg",
                "newUserLogin": true
            }
        ]
    }
}
```

4. Save the file and start Seerr.

Existing Seerr users can link their authentik account from **Profile** > **Settings** > **Linked Accounts** by clicking **Link Account** and selecting **authentik**.

## Configuration verification

To confirm that authentik is properly configured with Seerr, open Seerr and log in using the authentik button. You should be redirected to authentik and then redirected back to Seerr.

## Resources

- [Seerr OpenID Connect documentation](https://github.com/seerr-team/seerr/blob/preview-new-oidc/docs/using-seerr/settings/users/oidc.md)
- [Seerr OpenID Connect support discussion](https://github.com/seerr-team/seerr/discussions/2721)
