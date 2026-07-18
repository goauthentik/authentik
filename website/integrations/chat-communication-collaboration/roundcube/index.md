---
title: Integrate with Roundcube
sidebar_label: Roundcube
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Roundcube?

> Roundcube is a browser-based multilingual IMAP client with an application-like user interface. It provides the full functionality you expect from an email client, including MIME support, address book, folder manipulation, message searching and spell checking.
>
> -- https://roundcube.net

## Preparation

The following placeholders are used in this guide:

- `roundcube.company` is the FQDN of the Roundcube installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info Mail server support
Roundcube is often used alongside Postfix and Dovecot. Postfix sends/receives email (SMTP), Dovecot stores/retrieves mail (IMAP/POP3), and Roundcube acts as a webmail client.

Whichever mail server is used in conjunction with Roundcube must support XOAUTH2 for both SMTPD and IMAP/POP. A Postfix SMTP server can use Dovecot for authentication, which allows XOAUTH2 support in Postfix without requiring separate configuration.
:::

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Roundcube with authentik, you need to create a scope mapping and an application/provider pair in authentik.

### Create a property mapping

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **New Property Mapping**.
3. Select **Scope Mapping** and configure the following settings:
    - **Name**: Set an appropriate name.
    - **Scope name**: `dovecotprofile`
    - **Description**: Set an appropriate description, if desired.
    - **Expression**:
        ```python
        return {
            "name": request.user.name,
            "given_name": request.user.name,
            "family_name": "",
            "preferred_username": request.user.username,
            "nickname": request.user.username,
            "active": True,
        }
        ```
4. Click **Create**.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://roundcube.company/index.php/login/oauth`.
        - Select any available signing key.
        - Under **Advanced protocol settings**, set **Logout URI** to `https://roundcube.company/index.php/login/backchannel` and **Logout Method** to `Back-channel`.
        - Under **Advanced protocol settings** > **Scopes**, add the following scopes to **Selected Scopes**:
            - The `dovecotprofile` scope mapping that you previously created.
            - `authentik default OAuth Mapping: OpenID 'offline_access'`
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

## Roundcube configuration

### Configure Roundcube OAuth2

Set the following variables in your Roundcube configuration file:

```php title="config/config.inc.php"
$config['oauth_provider'] = 'generic';
$config['oauth_provider_name'] = 'authentik';
$config['oauth_client_id'] = '<Client ID from authentik>';
$config['oauth_client_secret'] = '<Client Secret from authentik>';
$config['oauth_auth_uri'] = 'https://authentik.company/application/o/authorize/';
$config['oauth_token_uri'] = 'https://authentik.company/application/o/token/';
$config['oauth_identity_uri'] = 'https://authentik.company/application/o/userinfo/';
$config['oauth_scope'] = 'email openid dovecotprofile offline_access';
$config['oauth_identity_fields'] = ['email'];
$config['oauth_cache'] = 'db';
```

:::tip Roundcube debugging
Add the following variable to your Roundcube configuration file to enable OAuth2 debugging:

```php title="config/config.inc.php"
$config['oauth_debug'] = true;
```

:::

### Configure Dovecot XOAUTH2

Add the XOAUTH2 and OAUTHBEARER authentication mechanisms and configure the OAuth2 database in your Dovecot configuration:

```text title="/etc/dovecot/dovecot.conf"
auth_mechanisms {
  oauthbearer = yes
  xoauth2 = yes
}

oauth2 {
  tokeninfo_url = https://authentik.company/application/o/userinfo/?access_token=
  introspection_url = https://<Client ID from authentik>:<Client Secret from authentik>@authentik.company/application/o/introspect/
  introspection_mode = post
  force_introspection = yes
  active_attribute = active
  active_value = true
  username_attribute = email
  ssl_client_ca_file = /etc/ssl/certs/ca-certificates.crt
}
```

:::tip Dovecot debugging
Add the following variables to your Dovecot configuration to enable debugging:

```text title="/etc/dovecot/dovecot.conf"
auth_debug = yes
auth_verbose = yes
```

:::

:::info Other email clients
With this setup, Dovecot can also be used with other email clients that support XOAUTH2 authentication. However, most commonly available clients, such as FairEmail for Android and Thunderbird, only provide built-in support for providers like Gmail and Outlook, with no option to configure custom mail servers.
:::

## Configuration verification

To confirm that authentik is properly configured with Roundcube, log out of Roundcube and open Roundcube. Select **Login via authentik**. A mailbox should open and you should be able to send and receive mail.

## Resources

- [Roundcube documentation - Configuration: OAuth2](https://github.com/roundcube/roundcubemail/wiki/Configuration:-OAuth2)
- [Roundcube OAuth2 defaults](https://github.com/roundcube/roundcubemail/blob/master/config/defaults.inc.php)
- [Dovecot CE documentation - OAuth2](https://doc.dovecot.org/main/core/config/auth/databases/oauth2.html)
