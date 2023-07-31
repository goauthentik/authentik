---
title: Firezone
---

<span class="badge badge--secondary">Support level: Community</span>

## What is Firezone

> Firezone is an open-source remote access platform built on WireGuard?, a modern VPN protocol that's 4-6x faster than OpenVPN.
> Deploy on your infrastructure and start onboarding users in minutes.
>
> -- https://www.firezone.dev

## Preparation

The following placeholders will be used:

-   `firezone.company` is the FQDN of the Firezone install.
-   `authenik` is the unique ID used to generate logins for this provider.
-   `authentik.company` is the FQDN of the authentik install.

Create an OAuth2/OpenID provider with the following parameters:

-   Client type: `Confidential`
-   Redirect URIs/Origins: `Redirect URI from Firezone Config`
-   Signing Key: `<Select your certificate>`
-   Click: `Finish`

Note the Client ID and Client Secret value. Create an application using the provider you've created above.

## Firezone Config

-   Click _Security_ under Settings
-   Under _Single Sign-On_, click on _Add OpenID Connect Provider_
-   Config ID: `authentik`
-   Label: `Text to display on the Login button`
-   Scope: `(leave default of "openid email profile")`
-   Response type: `(leave default of 'code')
-   Client ID: `Taken from Authentik Provider Config`
-   Client Secret: `Taken from Authentik Provider Config`
-   Discovery Document URI: `OpenID Configuration URL from Authentik`
-   Redirect URI: `https://firezone.company/auth/oidc/<ConfigID>/callback/`
    :::note
    You should be able to leave the default Rediret URL
    :::
-   Auto-create Users: Enabled in order to automatically provision users when signing in the first time.
-   Click _Save_,

Although local authentication is quick and easy to get started with, you can limit attack surface by disabling local authentication altogether. For production deployments it's usually a good idea to disable local authentication and enforce MFA through authentik.

:::info
In case something goes wrong with the configuration, you can temporarily re-enable local authentication via the REST API or by following instructions from https://www.firezone.dev/docs/administer/troubleshoot/#re-enable-local-authentication-via-cli.
:::

## Additional Resources

-   https://www.firezone.dev/docs/authenticate/oidc/
-   https://www.firezone.dev/docs/administer/troubleshoot/#re-enable-local-authentication-via-cli
