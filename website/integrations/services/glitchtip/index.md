---
title: Integrate with Glitchtip
sidebar_label: Glitchtip
---

# Glitchtip

<span class="badge badge--secondary">Support level: Community</span>

## What is Glitchtip

> Bugs are inevitable in web development. The important thing is to catch them when they appear. With GlitchTip, you can rest easy knowing that if your web app throws an error or goes down, you will be notified immediately. GlitchTip combines error tracking and uptime monitoring in one open-source package to keep you and your team fully up-to-date on the status of your projects.
>
> -- https://glitchtip.com/documentation

## Preparation

The following placeholders are used in this guide:

- `glitchtip.company` is the FQDN of the Glitchtip installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

Create an OAuth2/OpenID provider with the following parameters:

- Client Type: `Confidential`
- Redirect URIs: `https://glitchtip.company/accounts/oidc/authentik/login/callback/`

Note the Client ID and Client Secret values.

Create an application, using the provider you've created above. Note the slug of the application you've created.

## Glitchtip configuration

Configuration of OpenID Connect providers in Glitchtip is done using Django Admin.

1. Create a superuser using the `manage.py` script:

```
sudo docker exec -it glitchtip-web-1 ./manage.py createsuperuser
```

2. Go to `https://glitchtip.company/admin/socialaccount/socialapp/` and log in with the newly-created superuser.

3. Click **Add Social Application** and enter the following details:

- Provider: `OpenID Connect`
- Provider ID: `authentik` (should match the Redirect URI configured above)
- Provider Name: Whatever you want to appear on GlitchTip's log in button
- Client ID: &lt;Client ID from authentik>
- Secret key: &lt;Client Secret from authentik>
- Key: leave blank
- Settings: `{"server_url": "https://authentik.company/application/o/<Slug of the application from above>/"}`
  The URL should match the **OpenID Configuration Issuer** URL for the authentik provider.

This will add a **Log in with Authentik** button to the GlitchTip log in page. To add an authentik account to an existing GlitchTip account, log in using the username/password, click _Profile_, then click _Add Account_ in the _Social Auth Accounts_ section.
