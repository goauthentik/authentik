---
title: Integrate with Frappe/ERPNext
sidebar_label: Frappe
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Frappe?

> Frappe is a full stack, batteries-included, web framework written in Python and JavaScript.
>
> -- https://frappe.io/

## Preparation

The following placeholders are used in this guide:

- `frappe.company` is the FQDN of the Frappe installation.
- `authentik.company` is the FQDN of the authentik installation.

These instructions apply to Frappe Framework apps that use Social Login Key, including ERPNext.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Frappe with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://frappe.company/api/method/frappe.integrations.oauth2_logins.custom/authentik`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## Frappe configuration

1. Log in to Frappe as an administrator.
2. From the Frappe main menu, navigate to **Integrations** and select **Social Login Key**.
3. Click **+ New**.
4. Configure the following settings:
    - **Client Credentials**
        - **Enable Social Login**: enable this option.
        - **Provider Name**: `authentik`.
        - **Client ID**: Client ID from authentik.
        - **Client Secret**: Client Secret from authentik.
    - **Configuration**
        - **Sign ups**: `Allow`.
    - **Identity Details**
        - **Base URL**: `https://authentik.company`
    - **Client URLs**
        - **Authorize URL**: `/application/o/authorize/`
        - **Access Token URL**: `/application/o/token/`
        - **Redirect URL**: `/api/method/frappe.integrations.oauth2_logins.custom/authentik`
        - **API Endpoint**: `/application/o/userinfo/`
    - **Client Information**
        - **Auth URL Data**:

            ```json
            {
                "response_type": "code",
                "scope": "openid email profile"
            }
            ```

5. Click **Save**.

## Configuration verification

To confirm that authentik is properly configured with Frappe, log out of Frappe and click the login button for your configured provider. A successful login should redirect you to authentik and return you to Frappe after authentication.

## Resources

- [Frappe Docs - Adding Social Login Provider](https://docs.frappe.io/framework/user/en/guides/app-development/adding-social-login-provider)
- [Frappe Docs - How To Enable Social Logins](https://docs.frappe.io/framework/user/en/guides/deployment/how-to-enable-social-logins)
- [Frappe Docs - OpenID Connect and Frappe social login](https://docs.frappe.io/framework/user/en/guides/integration/openid_connect_and_frappe_social_login)
