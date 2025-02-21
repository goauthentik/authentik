---
title: Integrate with Portainer
sidebar_label: Portainer
support_level: community
---

## What is Portainer

> Portainer is a powerful, GUI-based Container-as-a-Service solution that helps organizations manage and deploy cloud-native applications easily and securely.
>
> -- https://www.portainer.io/

:::note
This is based on authentik 2021.7.3 and Portainer 2.6.x-CE. Portainer 2.6 supports OAuth without additional licenses, 1.x Series requires a paid license for OAuth.
:::

## Preparation

The following placeholders are used in this guide:

- `portainer.company` is the FQDN of Portainer installation.
- `authentik.company` is the FQDN of authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

### Step 1

In the Admin interface of authentik, under _Providers_, create an _OAuth2/OpenID Provider_ with these settings:

:::note
Only settings that have been modified from default have been listed.
:::

**Protocol Settings**

- Name: Portainer
- Client ID: Copy and Save this for Later
- Client Secret: Copy and Save this for later
- Redirect URIs/Origins: `https://portainer.company/`

### Step 2

Create an application which uses this provider. Optionally apply access restrictions to the application.

- Name: Portainer
- Slug: portainer
- Provider: Portainer
- Launch URL: https://portainer.company

## Portainer configuration

In Portainer, under _Settings_, _Authentication_, Select _OAuth_ and _Custom_

- Client ID: The 'Client ID' from the authentik provider
- Client Secret: The 'Client secret' from the authentik provider
- Authorization URL: `https://authentik.company/application/o/authorize/`
- Access Token URL: `https://authentik.company/application/o/token/`
- Resource URL: `https://authentik.company/application/o/userinfo/`
- Redirect URL: `https://portainer.company/`
- Logout URL: `https://authentik.company/application/o/portainer/end-session/`
- User Identifier: `preferred_username` (Or `email` if you want to use email addresses as identifiers)
- Scopes: `email openid profile`

:::note
Portainer by default shows commas between each item in the Scopes field. Do **NOT** use commas. Use a _space_
:::

![](./port1.png)

## Notes

:::note
Portainer Reference link: https://documentation.portainer.io/v2.0/auth/oauth/
:::
