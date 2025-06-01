---
title: Integrate with Mattermost Team Edition
sidebar_label: Mattermost Team Edition
support_level: community
---

## What is Mattermost Team Edition

> Mattermost is an open source, real-time collaboration platform. It provides chat, audio/video calling, screen sharing, and a plugin architecture for extending its capabilities. Mattermost Team Edition is the free, open-source version of the product.
>
> -- https://mattermost.com/

Mattermost Team Edition does not natively support generic single sign-on. With a manual edit to your configuration, you can use Mattermost's GitLab integration with authentik's OAuth2/OpenID Provider to authenticate using authentik. When this configuration is complete, Mattermost will display a login button that uses the GitLab icon on it, but it will be using your authentik system for authentication. You do not need to have GitLab installed or available. This setup does not use GitLab in any way.

## Preparation

The following placeholders are used in this guide:

- `mattermost.company` is the FQDN of the Mattermost installation.
- `authentik.company` is the FQDN of the authentik installation.

You will need direct access to the filesystem for your Mattermost Team Edition server. The configurations that are required can only be set by editing the `config.json` file directly. If you use a hosted version of Mattermost where you cannot access the files, you will not be able to complete these instructions.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Mattermost Team Edition with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, and the policy engine mode
    - Under UI Settings set the Launch URL to <kbd>https://<em>mattermost.company</em>/oauth/gitlab/login</kbd>
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to <kbd>https://<em>mattermost.company</em>/signup/gitlab/complete</kbd>
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Mattermost Team Edition configuration

1. Find the `config.json` file for your Mattermost installation ([documentation](https://docs.mattermost.com/configure/configuration-settings.html)). Open it in a text editor.

2. Change the `GitLabSettings` section of the file to look like the following. Insert your **client secret**, **client id**, and **slug** in the appropriate places.
```json
"GitLabSettings": {
    "Enable": true,
    "Secret": "**client secret**",
    "Id": "**client id**",
    "Scope": "",
    "AuthEndpoint": "https://authentik.company/application/o/authorize/",
    "TokenEndpoint": "https://authentik.company/application/o/token/",
    "UserAPIEndpoint": "https://authentik.company/application/o/userinfo/",
    "DiscoveryEndpoint": "https://authentik.company/application/o/**slug**/.well-known/openid-configuration",
    "ButtonText": "Login with authentik",
    "ButtonColor": "#000000"
},
```

3. On the Mattermost **Authentication** > **Signup** options (`https://mattermost.company/admin_console/authentication/signup`) make sure that **Enable Account Creation** is **true**.
4. After saving the changes to the `config.json` file, restart Mattermost.

## Additional Resources

- [Mattermost on Github](https://github.com/mattermost/mattermost)
- [Mattermost GitLab Authentication documentation](https://docs.mattermost.com/configure/authentication-configuration-settings.html#gitlab-oauth-2-0-settings)
- [Related blog post, in German, explaining this technique](https://ayedo.de/posts/mattermost-self-hosted-sso-mit-authentik/)