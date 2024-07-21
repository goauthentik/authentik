---
title: engomo
---

<span class="badge badge--secondary">Support level: Community</span>

## What is engomo

> engomo is an low-code app development platform to create enterprise apps for smartphones and tablets based on Android, iOS, or iPadOS.
> -- https://engomo.com/
>
> This guide explains how to set up engomo to use authentik as the OAuth provider for the application login on the smartphone/tablet and login to the admin WebGUI (composer).

## Preparation

The following placeholders will be used:

-   `engomo.company` is the FQDN of the Engomo install.
-   `authentik.company` is the FQDN of the authentik install.
-   `engomo.mapping` is the name of the Scope Mapping.
-   `ak.cert` = The authentik self-signed certificate you use for the service provider.

## authentik configuration

In authentik, create a new scope mapping. To do so, log in to the Admin interface, and navigate to **Customization-->Property Mapping** and then click **Create**.

-   `engomo.mapping` is the value for the Name.
-   `profile` is the value for the Scope name.
-   `return {"preferred_username": request.user.email,}` is the value for the Expression.

Create an application and OAuth2/OpenID provider in authentik. Use the following parameters for the OAuth2/OpenID provider::

Provider:

-   Name: `SP-engomo`
-   Client type: `Public`    
-   Redirect URIs/Origins (RegEx): `https://engomo.company/auth` and `com.engomo.engomo://callback/`
-   Signing Key: `ak.cert`
-   Scopes: `authentik default OAuth Mapping: OpenID 'email'` and `authentik default OAuth Mapping: OpenID 'offline_access'` and `authentik default OAuth Mapping: OpenID 'openid'` and `engomo.mapping`
-   Note the Client ID and Client Secret.

> [!IMPORTANT]
> Redirect URIs => write the values line by line.

Leave the rest as default values. You can of course adjust durations.

Application:

-   Name: `Engomo`
-   Slug: `engomo`
-   Launch URL: `https://engomo.company/`

## engomo configuration

Navigate to `https://engomo.company/composer` and log in with your admin credentials.

-   Select `Server`.
-   Select `Authentication`.
-   Add a new authentication method by clicking on the plus icon on the right.
-   Name: `authentik`
-   Type: `OpenID Connect`
-   Click **Create**.
-   Set the `Issuer` to the authentik FQDN `https://authentik.company/application/o/engomo`.
-   Set the `Client ID` to the Client ID from the SP-engomo provider that you created in authentik.
-   Set the `Client Secret` to the Client Secret from the SP-engomo provider that you created in authentik.

Leave the rest as default.

## engomo user creation

engomo doesn't create users automatically on signing in. So you have to do it manually right now.
Navigate to `https://engomo.company/composer` and log in with your admin credentials.

- Select `Users & Devices`.
- Click the plus button next in the Users section.
- Select `authentik` as the Authenticator in the dropdown.
- Create your user by typing in the email as the Username used in authentik.

At this point you are done.

## Test the login

- Open a browser of your choice and open the URL `https://engomo.company`.
- Enter the created user's email address and click the small arrow icon to log in.
- You should be redirected to authentik with all its login flows you have created by yourself.
- If you are redirected back to the `https://engomo.company/composer` URL you did everything correct.

> [!IMPORTANT]
> You will only have access to the app or composer page if you granted the permission to the newly created user of course.
