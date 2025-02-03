---
title: Integrate with AdventureLog
sidebar_label: AdventureLog
---

# Integrate with AdventureLog

<span class="badge badge--secondary">Support level: Community</span>

## What is AdventureLog

> AdventureLog is a self-hosted travel tracker and trip planner. AdventureLog is the ultimate travel companion for the modern-day explorer.
>
> -- https://adventurelog.app/

## Preparation

The following placeholders are used in this guide:

- `https://adventurelog-server.company` is the URL used to access the AdventureLog **server** instance.
- `https://authentik.company` is the URL of the Authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

1. Create a new OAuth2/OpenID Provider under **Applications** > **Providers** using the following settings:
    - **Name**: AdventureLog
    - **Authentication flow**: default-authentication-flow
    - **Authorization flow**: default-provider-authorization-explicit-consent
    - **Client type**: Confidential
    - **Client ID**: Either create your own Client ID or use the auto-populated ID
    - **Client Secret**: Either create your own Client Secret or use the auto-populated secret
      :::note
      Take note of the `Client ID` and `Client Secret` as they are required when configuring AdventureLog.
      :::
    - **Redirect URIs/Origins (RegEx)**:
      :::note
      Make sure type is set to `RegEx` and the following RegEx is used.
      :::
        - `^https://adventurelog-server.company/accounts/oidc/.*$`
    - **Signing Key**: authentik Self-signed Certificate
    - Leave everything else as default
2. Open the new provider you've just created.
3. Make a note of the **OpenID Configuration Issuer**.

## AdventureLog configuration

AdventureLog documentation can be found here: https://adventurelog.app/docs/configuration/social_auth/authentik.html

This configuration is done in the Admin Panel. You can either launch the panel directly from the `Settings` page or navigate to `/admin` on your AdventureLog server.

1. Login to AdventureLog as an administrator and navigate to the `Settings` page.
2. Scroll down to the `Administration Settings` and launch the admin panel.
3. In the admin panel, navigate to the `Social Accounts` section and click the add button next to `Social applications`. Fill in the following fields:

    - Provider: `OpenID Connect`
    - Provider ID: Authentik Client ID
    - Name: `Authentik`
    - Client ID: Authentik Client ID
    - Secret Key: Authentik Client Secret
    - Key: can be left blank
    - Settings: (make sure http/https is set correctly)

    ```json
    {
        "server_url": "https://authentik.company/application/o/[YOUR_SLUG]/"
    }
    ```

:::warning
`localhost` is most likely not a valid `server_url` for Authentik in this instance because `localhost` is the server running AdventureLog, not Authentik. You should use the IP address of the server running Authentik or the domain name if you have one.
:::

- Sites: move over the sites you want to enable Authentik on, usually `example.com` and `www.example.com` unless you renamed your sites.

4. Save the configuration.

Ensure that the Authentik server is running and accessible by AdventureLog. Users should now be able to log in to AdventureLog using their Authentik account.

## Linking to Existing Account

If a user has an existing AdventureLog account and wants to link it to their Authentik account, they can do so by logging in to their AdventureLog account and navigating to the `Settings` page. There is a button that says `Launch Account Connections`, click that and then choose the provider to link to the existing account.

## Troubleshooting

### 404 error when logging in.

Ensure the `https://adventurelog-server.company/accounts` path is routed to the backend, as it shouldn't hit the frontend when it's properly configured.

### Authentik - No Permission

In the Authentik instance, check access to the AdventureLog application from a specific user by using the Check Access/Test button on the Application dashboard. If the user doesn't have access, you can add an existing user/group policy to give your specific user/group access to the AdventureLog application.
