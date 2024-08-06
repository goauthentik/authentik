---
title: Frappe Helpdesk
---

<span class="badge badge--secondary">Support level: Community</span>

:::note
These instructions apply to all projects in the Frappe Family.
:::

## What is Frappe Helpdesk

> Frappe Helpdesk is an open source ticketing tool based on Frappe Framework.
>
> -- https://frappe.io/helpdesk

## Preparation

The following placeholders will be used:

-   `frappe.company` is the FQDN of the Service install.
-   `authentik.company` is the FQDN of the authentik install.
-   `provider` is the name for the social login provider in Frappe.

## authentik configuration

1. Create a new OAuth2/OpenID Provider under **Applications** > **Providers** using the following settings:
    - **Name**: Frappe
    - **Authentication flow**: default-authentication-flow
    - **Authorization flow**: default-provider-authorization-explicit-consent
    - **Client type**: Confidential
    - **Client ID**: Either create your own Client ID or use the auto-populated ID
    - **Client Secret**: Either create your own Client Secret or use the auto-populated secret
      :::note
      Take note of the `Client ID` and `Client Secret` as they are required when configuring Immich.
      :::
    - **Redirect URIs/Origins (RegEx)**:
        - `https://frappe.company/api/method/frappe.integrations.oauth2_logins.custom/provider`
    - **Scopes**: `email`, `openid`, `profile`
    - **Subject mode**: `Based on the Users's username`
      :::danger
      This assumes you have made usernames immutable.
      :::
    - **Include claims in id_token**: `True`
    - Leave everything else as default

## Service configuration

1. In Frappe main menu, navigate to Integrations, then to Social Login Key.

Add a new Social login Key using `+ Add Social Login Key` on top right.
![](./frappe1.png)

2.  Enter the following settings:

        In Client Credentials section:
        - Enable Social Login: Turn the checkmark to the _on_ position.
        - Client ID: _CLIENT_ID_
        - Client Secret: _CLIENT_SECRET_

        In Configuration section:
        - Sign ups: Allow

    ![](./frappe2.png)

        In Identity Details section:
        - Base URL: `https://authentik.company/`
        - In Client URLs section:
        - Authorize URL: `/application/o/authorize/`
        - Access Token URL: `/application/o/token/`
        - Redirect URL: `/api/method/frappe.integrations.oauth2_logins.custom/provider/`
        - API Endpoint: `/application/o/userinfo/`

    ![](./frappe3.png)

        In Client Information:
        - Auth URL Data: `{"response_type": "code", "scope": "email profile openid"}`

    ![](./frappe4.png)
