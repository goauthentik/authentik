---
title: Integrate with Mattermost Team Edition
sidebar_label: Mattermost Team Edition
support_level: community
---

## What is Mattermost Team Edition

> Mattermost is an open source, real-time collaboration platform. It provides chat, audio/video calling, screen sharing, and a plugin architecture for extending its capabilities. Mattermost Team Edition is the free, open-source version of the product.
>
> -- https://mattermost.com/

:::info
Mattermost Team Edition does not natively support generic single sign-on. However, you can manually configure Mattermost to use its GitLab integration for authentication via authentik’s OAuth2/OpenID Provider. This requires editing the `config.json` file directly, as the necessary settings are not available through the web interface. If you are using a hosted version of Mattermost without filesystem access, you will not be able to complete this setup. Once configured, Mattermost will display a login button with the GitLab icon, but authentication will be handled entirely by authentik. GitLab itself is not required or used in any way.
:::

## Preparation

The following placeholders are used in this guide:

- `mattermost.company` is the FQDN of the Mattermost installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Mattermost Team Edition with authentik, you need to create property mappings and an application/provider pair in authentik.

### Create property mappings

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**. Create a **Scope Mapping** with the following settings:
    - **Name**: `mattermost-username`
    - **Scope Name**: `username`
    - **Description**: `Maps the user's authentik username to the username field for Mattermost authentication.`
    - **Expression**:
        ```python
        return {
            "username": request.user.username,
        }
        ```

:::info
The following `id` property mapping is optional. If omitted, Mattermost will generate user IDs based on email addresses, resulting in names such as `person-example.com` for `person@example.com`. Since these IDs serve as nicknames, this format may be undesirable.
:::

3. If desired, click **Create** again, and create another **Scope Mapping** with the following settings:
    - **Name**: `mattermost-id`
    - **Scope Name**: `id`
    - **Description**: `Maps the user's Mattermost ID or primary key to the id field for Mattermost authentication.`
    - **Expression**:
        ```python
        return {
            "id": request.user.attributes.get("mattermostId", request.user.pk),
        }
        ```

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, and the policy engine mode.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to `https://mattermost.company/signup/gitlab/complete`.
    - Select any available signing key.
    - Under **Advanced protocol settings**, add the scopes you just created to the list of selected scopes.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Mattermost Team Edition configuration

To support the integration of Mattermost Team Edition with authentik, you'll need to update the `config.json` file of your Mattermost deployment:

1. Modify the `GitLabSettings` section to look like the following:

```json showLineNumbers title="/opt/mattermost/config/config.json"
"GitLabSettings": {
    "Enable": true,
    "Secret": "<client_secret>",
    "Id": "<client_id>",
    "Scope": "",
    "AuthEndpoint": "https://authentik.company/application/o/authorize/",
    "TokenEndpoint": "https://authentik.company/application/o/token/",
    "UserAPIEndpoint": "https://authentik.company/application/o/userinfo/",
    "DiscoveryEndpoint": "https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration",
    "ButtonText": "Log in with authentik",
    "ButtonColor": "#000000"
},
```

2. Log in to Mattermost as an administrator and navigate to the System Console. Go to **Authentication** > **Signup** options (`https://mattermost.company/admin_console/authentication/signup`) and make sure that **Enable Account Creation** is set to **true**.
3. Restart Mattermost to apply the changes.

## Configuration verification

To verify the integration of authentik with Mattermost Team Edition, log out and attempt to log back in. You should see a button called "Log in with authentik" on the login page, and a successful login should redirect you back to Mattermost Team Edition without any errors.

## Additional Resources

- [Mattermost on Github](https://github.com/mattermost/mattermost)
- [Mattermost GitLab Authentication documentation](https://docs.mattermost.com/configure/authentication-configuration-settings.html#gitlab-oauth-2-0-settings)
- [Related blog post, in German, explaining this technique](https://ayedo.de/posts/mattermost-self-hosted-sso-mit-authentik/)
