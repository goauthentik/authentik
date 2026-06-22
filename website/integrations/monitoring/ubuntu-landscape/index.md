---
title: Integrate with Ubuntu Landscape
sidebar_label: Ubuntu Landscape
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";
import TabItem from "@theme/TabItem";
import Tabs from "@theme/Tabs";

## What is Ubuntu Landscape?

> Landscape is Canonical's systems management tool for managing Ubuntu machines through a web interface or API.
>
> -- https://ubuntu.com/landscape

## Preparation

The following placeholders are used in this guide:

- `landscape.company` is the FQDN of the Landscape server.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

Landscape uses the OpenID Connect protocol for single sign-on.

:::warning User and role management
Landscape uses OIDC only for authentication. Invite users and assign roles and permissions in Landscape. Existing Landscape users cannot be upgraded to OIDC authentication; Canonical recommends recreating those users.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Landscape with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the application **slug** because it will be required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add the **Redirect URI** for your Landscape version:
            - For Landscape 26.04 LTS, add a **Redirect URI** of type `Strict` `Authorization` as `https://landscape.company/new_dashboard/handle-auth/oidc`.
            - For Landscape 24.04 LTS and Landscape 23.03 ESM, add a **Redirect URI** of type `Strict` `Authorization` as `https://landscape.company/login/handle-openid`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

## Landscape configuration

On the Landscape server, edit `/etc/landscape/service.conf` and add the OIDC configuration for your Landscape version.

<Tabs
defaultValue="landscape-2604"
values={[
{ label: "Landscape 26.04 LTS", value: "landscape-2604" },
{ label: "Landscape 24.04 LTS / 23.03 ESM", value: "landscape-2404-2303" },
]}>
<TabItem value="landscape-2604">

Add the following configuration under the `[appserver]` section:

```ini title="/etc/landscape/service.conf"
[appserver]
oidc_issuer = https://authentik.company/application/o/<application_slug>/
oidc_client_id = <Client ID from authentik>
oidc_client_secret = <Client Secret from authentik>
```

</TabItem>

<TabItem value="landscape-2404-2303">

Add the following configuration under the `[landscape]` section:

```ini title="/etc/landscape/service.conf"
[landscape]
oidc-issuer = https://authentik.company/application/o/<application_slug>/
oidc-client-id = <Client ID from authentik>
oidc-client-secret = <Client Secret from authentik>
```

</TabItem>
</Tabs>

After making these changes, restart the Landscape services:

```shell
sudo lsctl restart
```

## Configuration verification

To confirm that authentik is properly configured with Landscape, open Landscape and sign in with OpenID Connect. After the authentik login flow completes, verify that the invited user can access Landscape with the expected Landscape role.

## Resources

- [Canonical Landscape documentation - How to enable OIDC authentication](https://documentation.ubuntu.com/landscape/how-to-guides/external-authentication/openid-connect-oidc/)
- [Canonical Landscape documentation - The service.conf file](https://documentation.ubuntu.com/landscape/reference/config/service-conf/)
