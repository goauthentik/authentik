---
title: Integrate with DokuWiki
sidebar_label: DokuWiki
support_level: community
---

## What is DokuWiki

From https://en.wikipedia.org/wiki/DokuWiki

> DokuWiki is a wiki application licensed under GPLv2 and written in the PHP programming language. It works on plain text files and thus does not need a database. Its syntax is similar to the one used by MediaWiki. It is often recommended as a more lightweight, easier to customize alternative to MediaWiki.

## Preparation

The following placeholders are used in this guide:

- `dokuwiki.company` is the FQDN of the DokiWiki installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of DocuWiki with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can create only an application, without a provider, by clicking **Create**.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID** and **Client Secret** values because they will be required later.
    - Set a `Strict` redirect URI to <kbd>https://<em>docuwiki.company</em>/doku.php</kbd>.
    - Select any available signing key.
    - Under **Advanced Protocol Settings**, add the following OAuth mapping under **Scopes**: `authentik default OAuth Mapping: OpenID 'offline_access'`
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## DokuWiki configuration

In DokuWiki, navigate to the _Extension Manager_ section in the _Administration_ interface and install

- https://www.dokuwiki.org/plugin:oauth
- https://www.dokuwiki.org/plugin:oauthgeneric

Navigate to _Configuration Settings_ section in the _Administration_ interface and change _Oauth_ and _Oauthgeneric_ options:

For _Oauth_:

- Check the _plugin»oauth»register-on-auth_ option

For _Oauthgeneric_:

- plugin»oauthgeneric»key: The Application UID
- plugin»oauthgeneric»secret: The Application Secret
- plugin»oauthgeneric»authurl: https://authentik.company/application/o/authorize/
- plugin»oauthgeneric»tokenurl: https://authentik.company/application/o/token/
- plugin»oauthgeneric»userurl: https://authentik.company/application/o/userinfo/
- plugin»oauthgeneric»authmethod: Bearer Header
- plugin»oauthgeneric»scopes: email, openid, profile, offline_access
- plugin»oauthgeneric»needs-state: checked
- plugin»oauthgeneric»json-user: preferred_username
- plugin»oauthgeneric»json-name: name
- plugin»oauthgeneric»json-mail: email
- plugin»oauthgeneric»json-grps: groups

![](./dokuwiki_oauth_generic.png)

In the _Configuration Settings_ section in the _Administration_ interface navigate to _Authentication_ and activate _oauth_ in _Authentication backend_.
