---
title: Engomo Composer + App Login
---

<span class="badge badge--secondary">Support level: Community</span>

## What is engomo

> engomo is an low-code app development platform to create enterprise apps for smartphones and tablets based on Android, iOS, or iPadOS.
> -- https://engomo.com/
>
> This guide explains how to set up engomo to use authentik as the OAUTH provider for the application login on the smartphone/tablet and login to the admin WebGUI (composer).

## Preparation

The following placeholders will be used:

-   `engomo.company` is the FQDN of the Engomo install.
-   `authentik.company` is the FQDN of the authentik install.
-   `engomo.mapping` is the name of the Scope Mapping.
-   `ak.cert` = The authentik self-signed certificate you use for the service provider.

## Custom Property Mapping

Create a new Scope Mapping under the Customization settings (Property Mapping).

-   `engomo.mapping` is the value for the Name.
-   `profile` is the value for the Scope name.
-   `return {"preferred_username": request.user.email,}` is the value for the Expression.

Create an application and OAuth2/OpenID Provider in authentik. Create a OAuth2/OpenID Provider with the following parameters:

Provider:

-   Name: `SP-engomo`
-   Client type: `Public`    
-   Redirect URIs/Origins (RegEx) #1: `https://engomo.company/auth` (for composer)
-   Redirect URIs/Origins (RegEx) #2: `com.engomo.engomo://callback/` (for app)
-   Signing Key: `ak.cert`
-   Scopes: `authentik default OAuth Mapping: OpenID 'email'`
-   Scopes: `authentik default OAuth Mapping: OpenID 'offline_access'`
-   Scopes: `authentik default OAuth Mapping: OpenID 'openid'`
-   Scopes: `engomo.mapping`
-   Note the Client ID and Client Secret.

> [!IMPORTANT]
> Redirect URIs => write the values line by line.

Lave the rest as default values. You can of course adjust durations.

Application:

-   Name: `Engomo`
-   Slug: `engomo`
-   Launch URL: `https://engomo.company/`

## engomo configuration

Navigate to `https://engomo.company/composer` and login with your admin credentials.

-   Select `Server`.
-   Select `Authentication`.
-   Add a new authentication method by clicking on the plus icon on the right.
-   Name: `authentik`
-   Type: `OpenID Connect`
-   Click on Create.
-   Set the `Issuer` to the authentik FQDN `https://authentik.company/application/o/engomo`.
-   Set the `Client ID` to the Client ID from the SP-engomo provider inside authentik.
-   Set the `Client Secret` to the Client Secret from the SP-engomo provider inside authentik.

Leave the rest as default.

## Engomo User Creation

Engomo doesn't create users automatically on signing in. So you have to do it manually right now.
Navigate to `https://engomo.company/composer` and login with your admin credentials.

- Select `Users & Devices`.
- Click the plus button next in the Users section.
- Select `authentik` as the Authenticator in the dropdown.
- Create your user by typing in the email as the Username used in authentik.
