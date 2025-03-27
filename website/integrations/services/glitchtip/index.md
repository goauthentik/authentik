---
title: Integrate with Glitchtip
sidebar_label: Glitchtip
support_level: community
---

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

To support the integration of Glitchtip with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can create only an application, without a provider, by clicking **Create**.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to <kbd>https://<em>glitchtip.company</em>/accounts/oidc/authentik/login/callback/</kbd>.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

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
