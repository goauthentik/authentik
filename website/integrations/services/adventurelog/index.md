---
title: Integrate with AdventureLog
sidebar_label: AdventureLog
support_level: community
---

## What is AdventureLog

> AdventureLog is a self-hosted travel tracker and trip planner. AdventureLog is the ultimate travel companion for the modern-day explorer.
>
> -- https://adventurelog.app/

## Preparation

The following placeholders are used in this guide:

- `https://adventurelog.company` is the FQDN of the AdventureLog server installation.
- `https://authentik.company` is the FQDN of the authentik installation.

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
        - `^https://adventurelog.company/accounts/oidc/.*$`
    - **Signing Key**: authentik Self-signed Certificate
    - Leave everything else as default
2. Open the new provider you've just created.
3. Make a note of the **OpenID Configuration Issuer**.
4. Navigate to **Applications -> Applications** and create a new application that uses the provider you just created.

## AdventureLog configuration

AdventureLog documentation can be found here: https://adventurelog.app/docs/configuration/social_auth/authentik.html

This configuration is done in the Admin Panel. Launch the panel by clicking your user avatar in the navbar, selecting **Settings**, and then clicking **Launch Admin Panel**. Make sure you are logged in as an administrator for this to work.

Alternatively, navigate to `/admin` on your AdventureLog server.

1. In the admin panel, scroll down to the **Social Accounts** section and click **Add** next to **Social applications**. Fill in the following fields:

    - Provider: OpenID Connect
    - Provider ID: authentik Client ID
    - Name: authentik
    - Client ID: authentik Client ID
    - Secret Key: authentik Client Secret
    - Key: _should be left blank_
    - Settings: (make sure http/https is set correctly)

    ```json
    {
        "server_url": "https://authentik.company/application/o/[YOUR_SLUG]/"
    }
    ```

    - Sites: move over the sites you want to enable authentik on, usually `example.com` and `www.example.com` unless you renamed your sites.

:::warning
`localhost` is most likely not a valid `server_url` for authentik in this instance because `localhost` is the server running AdventureLog, not authentik. You should use the IP address of the server running authentik or the domain name if you have one.
:::

2. Save the configuration.

Ensure that the authentik server is running and accessible by AdventureLog. Users should now be able to log in to AdventureLog using their authentik account.

## Configuration validation

To validate the configuration, either link to an existing account as described below or naviage to the AdventureLog login page and click the **authentik** button to log in. You should be redirected to the authentik login page. After logging in, you should be redirected back to AdventureLog.

### Linking to Existing Account

If a user has an existing AdventureLog account and wants to link it to their authentik account, they can do so by logging in to their AdventureLog account and navigating to the **Settings** page. There is a button that says **Launch Account Connections**, click that and then choose the provider to link to the existing account.

## Troubleshooting

### 404 error when logging in.

Ensure the `https://adventurelog.company/accounts` path is routed to the backend, as it shouldn't hit the frontend when it's properly configured. For information on how to configure this, refer to the AdventureLog documentation on reverse proxy configuration [here](https://adventurelog.app/docs/install/getting_started.html).

### authentik - No Permission

Launch your authentik dashboard as an admin and find the AdventureLog app. Click **More details** then **Edit**. In the admin interface, click **Test** under **Check Access**. If you get a 403 error, you need to grant the user the correct permissions. This can be done by going to the user's profile and adding the correct permissions.
