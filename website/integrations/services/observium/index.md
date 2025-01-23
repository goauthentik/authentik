---
title: Integrate with Observium
sidebar_label: Observium
---

# Observium

<span class="badge badge--secondary">Support level: Community</span>

## What is Observium

> Observium is a network monitoring and management platform that provides real-time insight into network health and performance.
>
> -- https://observium.org

:::note
This is based on authentik 2024.6.0 and Observium CE 24.4.13528
:::

## Preparation

The following placeholders are used in this guide:

- `observium.company` is the FQDN of the Observium installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that have been changed from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

This guide assumes you already have a working Observium instance. It is recommended to install it with the install script, following the [instructions](https://docs.observium.org/) on Observium's website.

Apache2 comes bundled with Observium, but there is also a third party module, [mod_auth_openidc](https://github.com/OpenIDC/mod_auth_openidc), which is needed for this configuration to work.
Download the latest [release](https://github.com/OpenIDC/mod_auth_openidc/releases) of the project suitable for your machine.

This guide uses `libapache2-mod-auth-openidc_2.4.15.7-1.bookworm_amd64.deb` as an example.

Install the package:

```bash
apt install ./libapache2-mod-auth-openidc_2.4.15.7-1.bookworm_amd64.deb
```

## authentik configuration

1. In authentik, under **Providers**, create an **OAuth2/OpenID Provider** with these settings:

    - Name: Observium
    - Client ID: Copy this for later
    - Client Secret: Copy this for later
    - Redirect URIs/Origins: `https://observium.company/secure/redirect_uri` (This can be any location on the domain that doesn't point to actual content)
    - Signing Key: Select any available signing key

2. In authentik, under **Applications**, create an Application with these settings:

    - Name: Observium
    - Slug: observium
    - Provider: Select `Observium`

## Observium configuration

1. Edit the file `/etc/apache2/sites-available/000-default.conf` and add the following lines:

    ```apacheconf
    <VirtualHost *:80>
        ...

        OIDCProviderMetadataURL https://authentik.company/application/o/observium/.well-known/openid-configuration
        OIDCClientID <Client ID>
        OIDCClientSecret <Client Secret>
        OIDCRedirectURI https://observium.company/secure/redirect_uri
        OIDCCryptoPassphrase <Random string for security>
        OIDCCookieDomain observium.company
        OIDCXForwardedHeaders X-Forwarded-Host X-Forwarded-Proto
        OIDCPathScope "openid email profile"
        OIDCRemoteUserClaim preferred_username ^(.*)$ $1@authentik

        <Location />
        AuthType openid-connect
        Require valid-user
        </Location>

        ...
    </VirtualHost>
    ```

    Meaning of variables:

    - `OIDCRedirectURI` is the same URI that is set for the authentik Provider.
    - The `OIDCCryptoPassphrase` directive should be set to a random string, for more information, see [the official documentation](https://github.com/OpenIDC/mod_auth_openidc/blob/9c0909af71eb52283f4d3797e55d1efef64966f2/auth_openidc.conf#L15).
    - `OIDCXForwardedHeaders` is necessary if your instance is behind a reverse proxy. If omitted, the module does not accept information from these headers.
    - `OIDCRemoteUserClaim` tells the module how to construct a username based on your claims. The first argument selects the claim, while the second and third are RegEx search and replace expressions. [More info](https://github.com/OpenIDC/mod_auth_openidc/blob/9c0909af71eb52283f4d3797e55d1efef64966f2/auth_openidc.conf#L794)

2. Edit the Observium configuration. By default, it should be located at `/opt/observium/config.php`.

    Edit the following line:

    ```php
    $config['auth_mechanism'] = "remote";
    ```

    Add the following lines:

    ```php
    $config['auth_remote_userlevel'] = 10;
    $config['auth_remote_logout_url'] = "https://authentik.company/application/o/observium/end-session/";
    ```

    With this method, you can only assign one permission level to all users. Since Observium permits only a single authentication mechanism to be selected, it is recommended to set `auth_remote_userlevel` to 10. You can read about all of the user levels [here](https://docs.observium.org/user_levels/).

3. Restart the Apache2 service:

    ```bash
    service apache2 restart
    ```

    Now you should be able to log in to your Observium instance using authentik.
