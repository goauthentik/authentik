---
title: Glitchtip
---

<span class="badge badge--secondary">Support level: Community</span>

## What is Glitchtip

> Bugs are inevitable in web development. The important thing is to catch them when they appear. With GlitchTip, you can rest easy knowing that if your web app throws an error or goes down, you will be notified immediately. GlitchTip combines error tracking and uptime monitoring in one open-source package to keep you and your team fully up-to-date on the status of your projects.
>
> -- https://glitchtip.com/documentation

## Preparation

The following placeholders will be used:

-   `glitchtip.company` is the FQDN of the Glitchtip install.
-   `authentik.company` is the FQDN of the authentik install.

## authentik Configuration

Create an OAuth2/OpenID provider with the following parameters:

-   Client Type: `Confidential`
-   Redirect URIs: `https://glitchtip.company/auth/authentik`

Note the Client ID and Client Secret values.

Create an application, using the provider you've created above. Note the slug of the application you've created.

## Glitchtip Configuration

Configuration of OpenID Connect providers in Glitchtip is done using Django Admin.

Create a superuser:

```
sudo docker exec -it glitchtip-web-1 ./manage.py createsuperuser
```

Go to https://glitchtip.company/admin/socialaccount/socialapp/ and log in with the newly-created superuser.

Click "Add Social Application"

Enter the following details:

-   Provider: `OpenID Connect`
-   Provider ID: `authentik` (should match the Redirect URI configured above)
-   Provider Name: Whatever you want to appear on GlitchTip's log in button
-   Client ID: &lt;Client ID from Authentik>
-   Secret key: &lt;Client Secret from Authentik>
-   Key: leave blank
-   Settings: `{"server_url": "https://auth.d.sb/application/o/<Slug of the application from above>/"}`
    The URL should match the "OpenID Configuration Issuer" URL for the Authentik provider.

This will add a "Log in with Authentik" button to the GlitchTip log in page. To add an Authentik account to an existing GlitchTip account, log in using the username/password, click _Profile_, then click _Add Account_ in the _Social Auth Accounts_ section.
