---
title: Integrate with Observium
sidebar_label: Observium
support_level: community
---

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
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
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

To support the integration of Observium with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can create only an application, without a provider, by clicking **Create**.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to <kbd>https://<em>observium.company</em>/secure/redirect_uri</kbd>. Note that the Redirect URI can be anything, as long as it does not point to existing content.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

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
