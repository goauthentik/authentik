---
title: Writefreely
---

<span class="badge badge--secondary">Support level: Community</span>

## What is Writefreely

> An open source platform for building a writing space on the web.
>
> -- https://writefreely.org/

:::caution
Currently it is not possible to connect writefreely to authentik without making an adjustment in the database. See [here](https://github.com/writefreely/writefreely/issues/516) and [Writefreely Setup](https://goauthentik.io/integrations/services/writefreely/#writefreely-setup)
:::

## Preparation

The following placeholders will be used:

-   `writefreely.company` is the FQDN of the writefreely install.
-   `authentik.company` is the FQDN of the authentik install.

## authentik Configuration

### Step 1 - OAuth2/OpenID Provider

Create a OAuth2/OpenID Provider (under _Applications/Providers_) with these settings:

-   Name: writefreely
-   Redirect URI: `https://writefreely.company/oauth/callback/generic`

### Step 3 - Application

Create an application (under _Resources/Applications_) with these settings:

-   Name: Writefreely
-   Slug: writefreely
-   Provider: writefreely

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

-   https://writefreely.org/docs/latest/admin/config
