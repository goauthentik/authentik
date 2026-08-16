---
title: Integrate with osTicket
sidebar_label: osTicket
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is osTicket?

> osTicket is a web-based, open source user support/ticketing solution.
>
> -- https://osticket.com

## Preparation

The following placeholders are used in this guide:

- `osticket.company` is the FQDN of the osTicket installation.
- `authentik.company` is the FQDN of the authentik installation.

If osTicket is installed in a subdirectory, include that path before `/api/auth/oauth2` wherever this guide uses the osTicket redirect URI.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of osTicket with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://osticket.company/api/auth/oauth2`.
        - Select any available signing key.
        - Under **Advanced protocol settings**:
            - **Subject Mode**: `Based on the User's Email`
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## osTicket configuration

Before you enable OAuth2 authentication for agents, create any osTicket Agent accounts that should use authentik with the same email addresses as their authentik users. osTicket can create End User accounts during OAuth2 sign-in, but Agent accounts must already exist.

1. Download the **Authentication :: Oauth2** plugin from [the osTicket website](https://osticket.com/download) and place it into the `include/plugins` folder of your osTicket installation.
2. Log in to osTicket as an administrator and open the **Admin Panel**.
3. Navigate to **Manage** > **Plugins**.
4. Click **Add New Plugin** and follow the on-screen instructions to install the OAuth2 plugin.
5. After the plugin is installed, click the OAuth2 plugin, set **Status** to `Active`, and click **Save Changes**.
6. Open the **Instances** tab, click **Add New Instance**, select **OAuth2 - Other**, and configure the following settings:
    - On the **Instance** tab:
        - **Name**: enter a name for the instance.
        - Set **Status** to `Enabled`.
    - On the **Config** tab:
        - **Name**: `authentik`
        - **Authentication Target**: select `Agents Only`, `End Users Only`, or `Agents and End Users`.
        - **Authentication Label**: `authentik`
        - **Redirect URI**: `https://osticket.company/api/auth/oauth2`
        - **Client Id**: enter the Client ID from authentik.
        - **Client Secret**: enter the Client Secret from authentik.
        - **Authorization Endpoint**: `https://authentik.company/application/o/authorize/`
        - **Token Endpoint**: `https://authentik.company/application/o/token/`
        - **Resource Details Endpoint**: `https://authentik.company/application/o/userinfo/`
        - **Scopes**: `openid email profile`
    - Under **User Attributes Mapping**:
        - **Given Name**: `name`
        - Clear the **Surname** field.

7. Click **Save Changes**.
8. If you enabled OAuth2 authentication for agents, navigate to **Admin Panel** > **Agents** and confirm that the provider is available. Select **Use any available backend** so that administrators can still log in if OAuth2 authentication is unavailable.

## Configuration verification

To confirm that authentik is properly configured with osTicket, log out and open the osTicket integration from authentik. On the osTicket login page, click **Sign in with authentik** and authenticate with authentik.

## Resources

- [osTicket Docs - OAuth2 Guide](https://docs.osticket.com/en/latest/Guides/OAuth2%20Guide.html)
- [osTicket Docs - Okta Authentication (SSO) Guide](https://docs.osticket.com/en/latest/OAuth2/Okta%20Authentication%20%28SSO%29%20Guide.html)
