---
title: Integrate with WriteFreely
sidebar_label: WriteFreely
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is WriteFreely?

> An open source platform for building a writing space on the web.
>
> -- https://writefreely.org/

## Preparation

The following placeholders are used in this guide:

- `writefreely.company` is the FQDN of the WriteFreely installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of WriteFreely with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://writefreely.company/oauth/callback/generic`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

## WriteFreely configuration

Configure WriteFreely by editing `config.ini`. WriteFreely looks for this file in the current directory unless it is started with the `-c` flag.

```ini title="config.ini"
[oauth.generic]
client_id          = <Client ID from authentik>
client_secret      = <Client Secret from authentik>
host               = https://authentik.company
display_name       = authentik
token_endpoint     = /application/o/token/
inspect_endpoint   = /application/o/userinfo/
auth_endpoint      = /application/o/authorize/
scope              = openid profile email
map_user_id        = sub
map_username       = preferred_username
map_display_name   = name
map_email          = email
```

Restart WriteFreely for the changes to take effect.

### Configure registration _(optional)_

To disable local username and password authentication after you have tested OAuth sign-in, set `disable_password_auth` to `true` in the `[app]` section.

```ini title="config.ini"
[app]
disable_password_auth = true
```

WriteFreely uses the `open_registration` setting for both local registration and first-time OAuth sign-ins. If `open_registration` is set to `false`, users must already have a linked WriteFreely account or sign in through a valid invite.

To link an existing local account with authentik, log in to WriteFreely with local credentials before disabling password authentication. Then navigate to **Customize** > **Account Settings**. In the **Link External Accounts** section, click **Link authentik**.

## Configuration verification

To confirm that authentik is properly configured with WriteFreely, open WriteFreely and select the **Log in with authentik** option. A successful authentication redirects you to authentik and then returns you to WriteFreely as a signed-in user.

## Resources

- [WriteFreely documentation - Configuring WriteFreely](https://writefreely.org/docs/main/admin/config)
