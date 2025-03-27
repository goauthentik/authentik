---
title: Integrate with Writefreely
sidebar_label: Writefreely
support_level: community
---

## What is Writefreely

> An open source platform for building a writing space on the web.
>
> -- https://writefreely.org/

:::caution
Currently it is not possible to connect writefreely to authentik without making an adjustment in the database. See [here](https://github.com/writefreely/writefreely/issues/516) and [Writefreely Setup](https://goauthentik.io/integrations/services/writefreely/#writefreely-setup)
:::

## Preparation

The following placeholders are used in this guide:

- `writefreely.company` is the FQDN of the Writefreely installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Writefreely with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can create only an application, without a provider, by clicking **Create**.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to <kbd>https://<em>writefreely.company</em>/oauth/callback/generic</kbd>.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Writefreely Setup

### Database

Currently the column `access_token` is configured too small, so it needs to be adjusted

```
ALTER TABLE `oauth_users` MODIFY `access_token` varchar(2048);
```

### Configuration

Configure Writefreely settings by editing the `config.ini` and add the following:

So that new users can be created the following variable must be set to true

```
open_registration     = false
```

To disable the local login/registration use the following setting (this is useful because writefreely attracts a lot of spam)

```
disable_password_auth = false
```

The following settings must be made for oauth

```
[oauth.generic]
client_id          = <Client ID>
client_secret      = <Client Secret>
host               = https://authentik.company
display_name       = authentik
callback_proxy     =
callback_proxy_api =
token_endpoint     = /application/o/token/
inspect_endpoint   = /application/o/userinfo/
auth_endpoint      = /application/o/authorize/
scope              = openid profile email
allow_disconnect   = false
map_user_id        = sub
map_username       = nickname
map_display_name   = name
map_email          = email
```

Restart writefreely.service

## Account linking

If your usernames in authentik and WriteFreely are different, you might need to link your accounts before being able to use SSO.

To link the accounts, first log into Writefreely with local credentials, and then navigate to **Customize -->Account Settings**. In the option "Linked Accounts", click on "authentik".

## Additional Resources

- https://writefreely.org/docs/latest/admin/config
