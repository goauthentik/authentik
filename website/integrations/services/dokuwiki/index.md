---
title: DokuWiki
---

<span class="badge badge--secondary">Support level: Community</span>

## What is DokuWiki

> DokuWiki is a wiki application licensed under GPLv2 and written in the PHP programming language. It works on plain text files and thus does not need a database. Its syntax is similar to the one used by MediaWiki. It is often recommended as a more lightweight, easier to customize alternative to MediaWiki.
>
> -- https://en.wikipedia.org/wiki/DokuWiki

## Preparation

The following placeholders will be used:
- `dokuwiki.company` is the FQDN of the DokiWiki install.
- `authentik.company` is the FQDN of the authentik install.

## DokuWiki configuration

To configure DokuWiki:

1. Navigate to the **Extension Manager** section in the **Administration** interface.
2. Install the following plugins:
   - `https://www.dokuwiki.org/plugin:oauth`
   - `https://www.dokuwiki.org/plugin:oauthgeneric`

3. Go to **Configuration Settings** in the **Administration** interface.
4. Update the **Oauth** and **Oauthgeneric** options:
   - For **Oauth**:
     - Check the **plugin»oauth»register-on-auth** option
   - For **Oauthgeneric**:
     - **plugin»oauthgeneric»key**: The authentik application ID
     - **plugin»oauthgeneric»secret**: The authentik application secret
     - **plugin»oauthgeneric»authurl**: `https://authentik.company/application/o/authorize/`
     - **plugin»oauthgeneric»tokenurl**: `https://authentik.company/application/o/token/`
     - **plugin»oauthgeneric»userurl**: `https://authentik.company/application/o/userinfo/`
     - **plugin»oauthgeneric»authmethod**: Bearer Header
     - **plugin»oauthgeneric»scopes**: `email`, `openid`, `profile`, `offline_access`
     - **plugin»oauthgeneric»needs-state**: checked
     - **plugin»oauthgeneric»json-user**: `preferred_username`
     - **plugin»oauthgeneric»json-name**: `name`
     - **plugin»oauthgeneric»json-mail**: `email`
     - **plugin»oauthgeneric»json-grps**: `groups`

![](./dokuwiki_oauth_generic.png)

5. In **Configuration Settings**, go to **Authentication** and activate **oauth** in **Authentication backend**.

## authentik configuration

### Provider

To set up the provider in authentik:

1. Go to **Providers** and create an **OAuth2/OpenID Provider**.
2. Configure the following settings:
   - **Redirect URI**: The **Callback URL / Redirect URI** from **plugin»oauth»info**, usually `dokuwiki.company/doku.php`
   - **Signing Key**: Select any available key
3. Take note of the **client ID** and **client secret**, then save the provider.

:::info
To prevent users from needing to log in again when the access token expires, include the **offline_access** scope in both authentik and DokuWiki. This allows DokuWiki to use refresh tokens.
:::

### Application

To create an application in authentik:

1. Navigate to **Applications** under the **Applications tab**.
2. Set the provider to the one you previously created.
3. Fill out the remaining of the values to your liking and click **Create**.
