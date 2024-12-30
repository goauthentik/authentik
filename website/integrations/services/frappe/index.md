---
title: Integrate with Frappe Helpdesk
sidebar_label: Frappe Helpdesk
---

# Frappe Helpdesk

<span class="badge badge--secondary">Support level: Community</span>

:::note
These instructions apply to all projects in the Frappe Family.
:::

## What is Frappe Helpdesk

> Frappe Helpdesk is an open source ticketing tool based on Frappe Framework.
>
> -- https://frappe.io/helpdesk

## Preparation

The following placeholders are used in this guide:

- `frappe.company` is the FQDN of the Frappe install.
- `authentik.company` is the FQDN of the authentik install.
- `provider` is the name for the social login provider in Frappe.

## authentik configuration

1. Log in to authentik as an admin, and go to the Admin interface.
2. Create a new OAuth2/OpenID Provider under **Applications** -> **Providers** using the following settings:

    - **Name**: Frappe
    - **Client type**: Confidential
    - **Client ID**: Use the auto-populated ID
    - **Client Secret**: Use the auto-populated secret
    - **Redirect URIs/Origins (RegEx)**:
        - `https://frappe.company/api/method/frappe.integrations.oauth2_logins.custom/provider`
    - **Scopes**: `email`, `openid`, `profile`
    - **Subject mode**: `Based on the Users's username`
    - **Include claims in id_token**: `True`
    - Leave everything else as default

    Take note of **Client ID** and **Client Secret** as you will need them later.

3. Create a new application under **Applications** -> **Applications**, pick a name and a slug, and assign the provider that you have just created.

## Frappe configuration

1. From the Frappe main menu, navigate to **Integrations**, then to **Social Login Key**.

Add a new Social login Key using the black button on top right.
![](./frappe1.png)

2.  Enter the following settings:

        - In the **Client Credentials** section:
            - Enable Social Login: Turn the checkmark to the _on_ position.
            - Client ID: _client-id-from-authentik_
            - Client Secret: _client-secret-from-authentik_

        - In the **Configuration** section:
            - Sign ups: Allow

    ![](./frappe2.png)

        - In the **Identity Details** section:
            - Base URL: `https://authentik.company/`
            - In Client URLs section:
            - Authorize URL: `/application/o/authorize/`
            - Access Token URL: `/application/o/token/`
            - Redirect URL: `/api/method/frappe.integrations.oauth2_logins.custom/provider/`
            - API Endpoint: `/application/o/userinfo/`

    ![](./frappe3.png)

        - In the **Client Information** section:
            - Auth URL Data: `{"response_type": "code", "scope": "email profile openid"}`

    ![](./frappe4.png)

3.  Press the black **Save** button on the top right.

## Verification

1. Go to `https://frappe.company` from Incognito mode.
2. Click **Login with provider** on the login screen.
3. Authorize with authentik.
4. You will be redirected to home screen of Frappe application.
