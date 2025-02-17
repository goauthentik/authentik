---
title: Integrate with DokuWiki
sidebar_label: DokuWiki
---

# Integrate with DokuWiki

<span class="badge badge--secondary">Support level: Community</span>

## What is DokuWiki

> DokuWiki is an open source wiki application licensed under GPLv2 and written in the PHP programming language. It works on plain text files and thus does not need a database. Its syntax is similar to the one used by MediaWiki and it is often recommended as a more lightweight, easier to customize alternative to MediaWiki.
>
> -- https://en.wikipedia.org/wiki/DokuWiki

## Preparation

The following placeholders are used in this guide:

- `dokuwiki.company` is the FQDN of the DokiWiki installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of DocuWiki with authentik, you need to create an application/provider pair in authentik.

**Create an application and provider in authentik**

In the authentik Admin Interface, navigate to **Applications** > **Applications** and click **[Create with Provider](/docs/add-secure-apps/applications/manage_apps#add-new-applications)** to create an application and provider pair. (Alternatively you can create only an application, without a provider, by clicking **Create**.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID** and **Client Secret** values because they will be required later.
    - Set a `Strict` redirect URI to <kbd>https://<em>docuwiki.company</em>/doku.php</kbd>.
    - Select any available signing key.
    - Under **Advanced Protocol Settings**, add the following OAuth mapping under **Scopes**: `authentik default OAuth Mapping: OpenID 'offline_access'`
- **Configure Bindings** _(optional):_ you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user’s **My applications** page.

## DokuWiki configuration

From the **Administration** interface of your DocuWiki installation, navigate to **Extension Manager** and install the following extensions:

- https://www.dokuwiki.org/plugin:oauth
- https://www.dokuwiki.org/plugin:oauthgeneric

Then, under the **Configuration Settings** section, update the **oauth** and **oauthgeneric** options:

For **oauth**: - Select the following option: `plugin»oauth»register-on-auth`

:::warning
When using `preferred_username` as the user identifier, ensure that the [Allow users to change username setting](https://docs.goauthentik.io/docs/sys-mgmt/settings#allow-users-to-change-username) is disabled to prevent authentication issues. You can configure DocuWiki to use either the `sub` or `preferred_username` as the UID field under `plugin»oauthgeneric»json-user`. The `sub` option uses a unique, stable identifier for the user, while `preferred_username` uses the username configured in authentik.
:::

For **oauthgeneric**:

- Set `plugin»oauthgeneric»key` to the Client ID from authentik
- Set `plugin»oauthgeneric»secret` to the Client Secret from authentik
- Set `plugin»oauthgeneric»authurl` to <kbd>https://<em>authentik.company</em>/application/o/authorize/</kbd>
- Set `plugin»oauthgeneric»tokenurl` to <kbd>https://<em>authentik.company</em>/application/o/token/</kbd>
- Set `plugin»oauthgeneric»userurl` to <kbd>https://<em>authentik.company</em>/application/o/userinfo/</kbd>
- Set `plugin»oauthgeneric»authmethod` to `Bearer Header`
- Set `plugin»oauthgeneric»scopes` to `email, openid, profile, offline_access`
- Select `plugin»oauthgeneric»needs-state`
- Set `plugin»oauthgeneric»json-user` to `preferred_username`
- Set `plugin»oauthgeneric»json-name` to `name`
- Set `plugin»oauthgeneric»json-mail` to `email`
- Set `plugin»oauthgeneric»json-grps` to`groups`

![](./dokuwiki_oauth_generic.png)

Once that is done, navigate to the **Authentication** sub-section of the **Administration** interface's **Configuration Settings** section and enable **oauth** under **Authentication backend**.

## Ressources

- [DocuWiki OAuth plugin](https://www.dokuwiki.org/plugin:oauth)
- [DocuWiki plugin for generic OAuth](https://www.dokuwiki.org/plugin:oauthgeneric)

## Configuration verification

To verify that authentik is correctly configured with DocuWiki, log out and log back in through authentik. You should notice a new button on the login page.
