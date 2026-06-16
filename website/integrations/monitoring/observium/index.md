---
title: Integrate with Observium
sidebar_label: Observium
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Observium?

> Observium is a network monitoring and management platform that provides real-time insight into network health and performance.
>
> -- https://observium.org

## Preparation

The following placeholders are used in this guide:

- `observium.company` is the FQDN of the Observium installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

This guide assumes that you already have a working Observium instance served by Apache HTTP Server with [mod_auth_openidc](https://github.com/OpenIDC/mod_auth_openidc) installed and enabled. Observium does not have a native OpenID Connect integration, so this guide uses mod_auth_openidc to authenticate users with authentik and pass them to Observium through Apache `REMOTE_USER` authentication.

## authentik configuration

<RedirectURI20265Note />

To support the integration of Observium with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **slug** value because it will be required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://observium.company/secure/redirect_uri`. Note that the Redirect URI can be anything, as long as it does not point to existing content.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## Observium configuration

1. Edit the Apache virtual host that serves Observium and add the following directives inside the `<VirtualHost>` block:

    ```apacheconf title="/etc/apache2/sites-available/000-default.conf"
    <VirtualHost *:80>
        # Existing Observium configuration

        OIDCProviderMetadataURL https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration
        OIDCClientID <Client ID from authentik>
        OIDCClientSecret <Client Secret from authentik>
        OIDCRedirectURI https://observium.company/secure/redirect_uri
        OIDCCryptoPassphrase <random string>
        OIDCScope "openid email profile"
        OIDCRemoteUserClaim preferred_username ^(.*)$ $1@authentik

        <Location />
            AuthType openid-connect
            Require valid-user
        </Location>
    </VirtualHost>
    ```

    If Observium is behind a reverse proxy that sends `X-Forwarded-*` headers, also configure `OIDCXForwardedHeaders` with every forwarded header that reaches Apache, for example:

    ```apacheconf
    OIDCXForwardedHeaders X-Forwarded-Host X-Forwarded-Proto X-Forwarded-Port
    ```

2. Edit the Observium configuration:

    ```php title="/opt/observium/config.php"
    $config['auth_mechanism'] = "remote";
    $config['auth_remote_userlevel'] = 10;
    $config['auth_remote_logout_url'] = "https://authentik.company/application/o/<application_slug>/end-session/";
    ```

    With this method, Observium assigns the same permission level to all remotely authenticated users. The value `10` gives users administrator access. Choose the user level that fits your Observium access policy.

3. Restart the Apache2 service:

    ```bash
    service apache2 restart
    ```

## Configuration verification

To confirm that authentik is properly configured with Observium, open Observium. You should be redirected to authentik and returned to Observium after a successful login.

## Resources

- [Observium - Authentication](https://docs.observium.org/authentication/)
- [Observium - User Levels](https://docs.observium.org/user_levels/)
- [mod_auth_openidc - How to Use It](https://github.com/OpenIDC/mod_auth_openidc#how-to-use-it)
- [mod_auth_openidc - Configuration Options](https://github.com/OpenIDC/mod_auth_openidc/blob/master/auth_openidc.conf)
