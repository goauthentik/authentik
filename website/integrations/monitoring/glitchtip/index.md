---
title: Integrate with GlitchTip
sidebar_label: GlitchTip
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is GlitchTip?

> GlitchTip makes monitoring software easy. Track errors, monitor performance, and check site uptime all in one place.
>
> -- https://glitchtip.com/

## Preparation

The following placeholders are used in this guide:

- `glitchtip.company` is the FQDN of the GlitchTip installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of GlitchTip with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **slug** value because you will use it when configuring GlitchTip.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://glitchtip.company/accounts/oidc/authentik/login/callback/`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

## GlitchTip configuration

Configuration of OpenID Connect providers in GlitchTip is done using Django Admin.

1. If you do not already have a GlitchTip administrator account, create a superuser using the `manage.py` script:

```shell
sudo docker exec -it glitchtip-web-1 ./manage.py createsuperuser
```

2. Go to `https://glitchtip.company/admin/socialaccount/socialapp/` and log in with the superuser.

3. Click **Add Social Application** and enter the following details:
    - **Provider**: `OpenID Connect`
    - **Provider ID**: `authentik`
    - **Provider Name**: `authentik`
    - **Client ID**: `<Client ID from authentik>`
    - **Secret key**: `<Client Secret from authentik>`
    - **Settings**:

        ```json
        {
            "server_url": "https://authentik.company/application/o/<application_slug>/"
        }
        ```

4. Click **Save**.

The **Provider ID** value determines the callback path. If you use a provider ID other than `authentik`, update the redirect URI in the authentik provider to `https://glitchtip.company/accounts/oidc/<provider_id>/login/callback/`.

To add an authentik account to an existing GlitchTip account, log in with the existing username and password, click **Profile**, and then click **Add Account** in the **Social Auth Accounts** section.

## Configuration verification

To confirm that authentik is properly configured with GlitchTip, log out of GlitchTip and open the GlitchTip login page. Click the authentik login option and confirm that you are redirected to authentik for authentication and then back to GlitchTip.

## Resources

- [GlitchTip - Django Admin and Social Authentication](https://glitchtip.com/documentation/install/#django-admin)
- [django-allauth OpenID Connect provider documentation](https://docs.allauth.org/en/dev/socialaccount/providers/openid_connect.html)
