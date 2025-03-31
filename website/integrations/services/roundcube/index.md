---
title: Integrate with Roundcube
sidebar_label: Roundcube
support_level: community
---

## What is Roundcube

> **Roundcube** is a browser-based multilingual IMAP client with an application-like user interface.
> It provides full functionality you expect from an email client, including MIME support, address book, folder manipulation, message searching and spell checking
>
> -- https://roundcube.net

This integration describes how to use Roundcube's oauth support with authentik to automatically sign into an email account.
The mail server must support XOAUTH2 for both SMTPD and IMAP/POP. Postfix SMTP server can also use Dovecot for authentication which provides Postfix with xoauth2 capability without configuring it separately.

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.
- `roudcube.company` is the FQDN of the Roundcube installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Roundcube with authentik, you need to create an application/provider pair in authentik.

### Create property mappings

1. Log in to authentik as an admin, and open the authentik Admin interface.
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
        }
        ```

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to <kbd>https://<em>roundcube.company</em>/index.php?\_task=settings&\_action=plugin.oauth_redirect</kbd>.
    - Select any available signing key.
    - Under **Advanced protocol settings**, add the scope you just created to the list of selected scopes.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Roundcube Configuration

```
$config['oauth_provider'] = 'generic';
$config['oauth_provider_name'] = 'authentik';
$config['oauth_client_id'] = '<Client ID>';
$config['oauth_client_secret'] = '<Client Secret>';
$config['oauth_auth_uri'] = 'https://authentik.company/application/o/authorize/';
$config['oauth_token_uri'] = 'https://authentik.company/application/o/token/';
$config['oauth_identity_uri'] = 'https://authentik.company/application/o/userinfo/';
$config['oauth_scope'] = "email openid dovecotprofile";
$config['oauth_auth_parameters'] = [];
$config['oauth_identity_fields'] = ['email'];
```

## Dovecot Configuration

Add xoauth2 as an authentication mechanism and configure the following parameters in your Dovecot configuration.

```
tokeninfo_url = https://authentik.company/application/o/userinfo/?access_token=
introspection_url = https://<Client ID>:<Client Secret>@authentik.company/application/o/introspect/
introspection_mode = post
force_introspection = yes
active_attribute = active
active_value = true
username_attribute = email
tls_ca_cert_file = /etc/ssl/certs/ca-certificates.crt
```

:::note
With this setup Dovecot can also be used with other email clients that support XOAUTH2 authentication, however
most available software (including Fair Email for Android and Thunderbird) only come with support for Gmail,
Outlook etc with no way to configure custom email servers.
:::

## Additional Resources

Please refer to the following for further configuration information:

- https://roundcube.net
- https://github.com/roundcube/roundcubemail/wiki/Configuration:-OAuth2
- https://doc.dovecot.org/configuration_manual/authentication/oauth2/
