---
title: Integrate with Roundcube
sidebar_label: Roundcube
support_level: community
---

## What is Roundcube

> Roundcube is a browser-based multilingual IMAP client with an application-like user interface. It provides the full functionality you expect from an email client, including MIME support, address book, folder manipulation, message searching and spell checking.
>
> -- https://roundcube.net

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.
- `roudcube.company` is the FQDN of the Roundcube installation.

:::info
Roundcube is often used alongside Postfix and Dovecot. Postfix sends/receives email (SMTP), Dovecot stores/retrieves mail (IMAP/POP3), and Roundcube acts as a webmail client.

Whichever mail server is used in conjunction with Roundcube must support XOAUTH2 for both SMTPD and IMAP/POP. A Postfix SMTP server can use Dovecot for authentication, which allows XOAUTH2 support in Postfix without requiring separate configuration.
:::

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Roundcube with authentik, you need to create an application/provider pair in authentik.

### Create property mappings

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**. Create a **Scope Mapping** with the following settings:
    - **Name**: Set an appropriate name.
    - **Scope Name**: `dovecotprofile`
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

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to `https://roundcube.company/index.php?\_task=settings&\_action=plugin.oauth_redirect`.
    - Select any available signing key.
    - Under **Advanced protocol settings**:
        - Under **Scopes**, add `dovecotprofile` and `authentik default OAuth Mapping: OpenID 'offline_access'` to the list of selected scopes.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Roundcube configuration

Set the following variables in your Roundcube configuration file:

```sh title="config/config.inc.php"
$config['oauth_provider'] = 'generic';
$config['oauth_provider_name'] = 'authentik';
$config['oauth_client_id'] = '<client_ID>';
$config['oauth_client_secret'] = '<client_secret>';
$config['oauth_auth_uri'] = 'https://authentik.company/application/o/authorize/';
$config['oauth_token_uri'] = 'https://authentik.company/application/o/token/';
$config['oauth_identity_uri'] = 'https://authentik.company/application/o/userinfo/';
$config['oauth_scope'] = "email openid dovecotprofile offline_access";
$config['oauth_auth_parameters'] = [];
$config['oauth_identity_fields'] = ['email'];
```

:::tip Roundcube debugging
Add the following variable to your Roundcube configuration file to enable debugging:

```sh
$config['debug_level'] = 4;
```

:::

## Dovecot configuration

Add XOAUTH2 as an authentication mechanism and configure the following variables in your Dovecot configuration:

```sh title="/etc/dovecot/dovecot.conf"
tokeninfo_url = https://authentik.company/application/o/userinfo/?access_token=
introspection_url = https://<client_ID>:<client_secret>@authentik.company/application/o/introspect/
introspection_mode = post
force_introspection = yes
active_attribute = active
active_value = true
username_attribute = email
tls_ca_cert_file = /etc/ssl/certs/ca-certificates.crt
```

:::tip Dovecot debugging
Add the following variables to your Dovecot configuration to enable debugging:

```
auth_debug = yes
auth_verbose = yes
```

:::

:::info
With this setup, Dovecot can also be used with other email clients that support XOAUTH2 authentication. However, most commonly available clients, such as FairEmail for Android and Thunderbird, only provide built-in support for providers like Gmail and Outlook, with no option to configure custom mail servers.
:::

## Configuration verification

To verify that authentik is correctly integrated with Roundcube, first log out of Roundcube. Log in to roundcube using authentik credentials. A mailbox should open and you should be able to send and receive mail.

## References

- [Roundcube documentation - Configuration: OAuth2](https://github.com/roundcube/roundcubemail/wiki/Configuration:-OAuth2)
- [Dovecot documentation - Open Authentication v2.0 Database](https://doc.dovecot.org/main/core/config/auth/databases/oauth2.html)
