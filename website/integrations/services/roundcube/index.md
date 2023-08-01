---
title: Roundcube
---

<span class="badge badge--secondary">Support level: Community</span>

## What is Roundcube

> **Roundcube** is a browser-based multilingual IMAP client with an application-like user interface.
> It provides full functionality you expect from an email client, including MIME support, address book, folder manipulation, message searching and spell checking
>
> -- https://roundcube.net

This integration describes how to use Roundcube's oauth support with authentik to automatically sign into an email account.
The mail server must support XOAUTH2 for both SMTPD and IMAP/POP. Postfix SMTP server can also use Dovecot for authentication which provides Postfix with xoauth2 capability without configuring it separately.

## Preparation

The following placeholders will be used:

-   `authentik.company` is the FQDN of the authentik install.

Create a new oauth2 Scope Mapping which does not return the 'group' values and associate this mapping
in the provider settings instead of the default oauth mapping.

Under _Customization_ -> _Property Mappings_, create a _Scope Mapping_. Give it a name like "oauth2-Scope-dovecot". Set the scope name to `dovecotprofile` and the expression to the following

```
return {
    "name": request.user.name,
    "given_name": request.user.name,
    "family_name": "",
    "preferred_username": request.user.username,
    "nickname": request.user.username,
  	 #DO NOT INCLUDE groups
}
```

Create an application in authentik. Create an _OAuth2/OpenID Provider_ with the following parameters:

-   Client Type: `Confidential`
-   Scopes: OpenID, Email, and the scope you created above
-   Signing Key: Select any available key

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

-   https://roundcube.net
-   https://github.com/roundcube/roundcubemail/wiki/Configuration:-OAuth2
-   https://doc.dovecot.org/configuration_manual/authentication/oauth2/
