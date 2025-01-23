---
title: Integrate with engomo
sidebar_label: engomo
---

# engomo

<span class="badge badge--secondary">Support level: Community</span>

## What is engomo

> engomo is an low-code app development platform to create enterprise apps for smartphones and tablets based on Android, iOS, or iPadOS.
> -- https://engomo.com/
>
> This guide explains how to set up engomo to use authentik as the OAuth provider for the application login on the smartphone/tablet and login to the admin WebGUI (composer).

## Preparation

The following placeholders are used in this guide:

- `engomo.company` is the FQDN of the engomo installation.
- `authentik.company` is the FQDN of the authentik installation.
- `engomo.mapping` is the name of the Scope Mapping.
- `ak.cert` is the self-signed certificate that will be used for the service provider.

:::note
This documentation lists only the settings that have been changed from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

In authentik, create a new scope mapping. To do so, log in and navigate to the Admin interface, then go to **Customization --> Property Mapping** and click **Create**.

- `engomo.mapping` is the value of the Mapping's name.
- `profile` is the value for the Scope name.
- `return {"preferred_username": request.user.email}` is the value for the Expression.

Create an application and an OAuth2/OpenID provider in authentik. Use the following parameters for the OAuth2/OpenID provider:

**Provider:**

- Name: `SP-engomo`
- Client type: `Public`
- Redirect URIs/Origins (RegEx): `https://engomo.company/auth` and `com.engomo.engomo://callback/`
- Signing Key: `ak.cert`
- Scopes: `authentik default OAuth Mapping: OpenID 'email', 'offline_access', OpenID 'openid'` and `engomo.mapping`

> [!IMPORTANT]
> Redirect URIs => write the values line by line.

Leave the rest as default values. The durations can be changed as needed.

**Application:**

- Name: `engomo`
- Slug: `engomo`
- Launch URL: `https://engomo.company/`

## engomo configuration

Navigate to `https://engomo.company/composer` and log in with your admin credentials.

- Select `Server`.
- Select `Authentication`.
- Add a new authentication method by clicking on the plus icon on the right.
- Name: `authentik`
- Type: `OpenID Connect`
- Click **Create**.
- Set the `Issuer` to the authentik FQDN `https://authentik.company/application/o/engomo`.
- Set the `Client ID` to the Client ID from the SP-engomo provider that you created in authentik.
- Set the `Client Secret` to the Client Secret from the SP-engomo provider that you created in authentik.

Leave the rest as default.

## engomo user creation

engomo doesn't create users automatically when signing in. So you have to do it manually right now.
Navigate to `https://engomo.company/composer` and log in with your admin credentials.

- Select `Users & Devices`.
- Click the plus button next in the Users section.
- Select `authentik` as the Authenticator in the dropdown.
- Create your user by typing in the email as the Username used in authentik.

At this point you are done.

## Test the login

- Open a browser of your choice and open the URL `https://engomo.company`.
- Enter the created user's email address and click the small arrow icon to log in.
- You should be redirected to authentik (with the login flows you created) and then authentik should redirect you back to `https://engomo.company/composer` URL.
- If you are redirected back to the `https://engomo.company/composer` URL you did everything correct.

> [!IMPORTANT]
> The created user will only have access to the app or composer page if you granted the permission to the user of course.
