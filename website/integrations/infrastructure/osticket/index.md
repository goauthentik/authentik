---
title: Integrate with osTicket
sidebar_label: osTicket
support_level: community
---

## What is osTicket

> osTicket is a web-based, open source user support/ticketing solution.
>
> -- https://osticket.com

## Preparation

The following placeholders are used in this guide:

- `osticket.company` is the FQDN of the osTicket installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of osTicket with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **slug** as it will be required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **slug** values because they will be required later.
        - Set a `Strict` redirect URI to `https://osticket.company/osticket/api/auth/oauth2`.
        - Select any available signing key.
        - Under **Advanced Protocol Settings**:
            - **Subject Mode**: `Based on the User's Email`
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## osTicket configuration

1. Download the OAuth2 plugin from [the osTicket website](https://osticket.com/download) and place it into the `include/plugins` folder of your osTicket installation. Then 
2. Log in to osTicket as an administrator and navigate to the **Admin Panel** > **Manage** > **Plugins**. 
3. Click **Add New Plugins** and follow the onscreen instructions to install the OAuth2 plugin.
4. Once installed click on the newly installed OAuth2 plugin, set **Status** to **Active ** and then click **Save Changes**.
5. Navigate to **Instances**, click on **Add New Instance**, select **OAuth2 - Other** and set the following fields:
    - On the **Instance** tab:
        - Define the **Name**.
        - Set **Status** to `Enabled`.
    - On the **Config** tab:
        - **Name**: `authentik`
        - **Authentication Target**: `Agents Only` or `End Users Only` or `Agents and End Users`
        - **Authentication Label**: `authentik`
        - **Redirect URI**: `https://osticket.company/osticket/api/auth/oauth2`
        - **Client Id**: Set the Client ID from authentik.
        - **Client Secret**: Set the Client secret from authentik.
        - **Authorization Endpoint**: `https://authentik.company/application/o/authorize/`
        - **Token Endpoint**: `https://authentik.company/application/o/token/`
        - **Resource Details Endpoint**: `https://authentik.company/application/o/userinfo/`
        - **Scopes**: `email openid profile`

6. Click on **Save Changes**.

## Additional Resources

- https://docs.osticket.com/en/latest/Guides/OAuth2%20Guide.html
