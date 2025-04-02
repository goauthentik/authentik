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

To support the integration of Adventure Log with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Set a `Regex` redirect URI to <kbd>^https://<em>adventurelog.company</em>/accounts/oidc/.\*$</kbd>.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

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
