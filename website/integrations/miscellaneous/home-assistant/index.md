---
title: Integrate with Home Assistant
sidebar_label: Home Assistant
support_level: community
---

<!-- spellchecker:ignore christiaangoossens -->

## What is Home Assistant?

> Open source home automation that puts local control and privacy first. Powered by a worldwide community of tinkerers and DIY enthusiasts. Perfect to run on a Raspberry Pi or a local server.
>
> -- https://www.home-assistant.io/

## Preparation

The following placeholders are used in this guide:

- `hass.company` is the FQDN of the Home Assistant installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## Configuration methods

Home Assistant does not have support for any SSO protocols out of the box. Therefore, you must install a custom integration first. The Home Assistant community has developed multiple custom integrations for OIDC support:

- [cavefire/hass-openid](https://github.com/cavefire/hass-openid)
- [christiaangoossens/hass-oidc-auth](https://github.com/christiaangoossens/hass-oidc-auth)

Both use OpenID Connect to integrate Home Assistant with authentik securely, but each integration has its own values, security standards, and features.

You should evaluate which integration is the best fit for you before continuing with this guide.

import TabItem from "@theme/TabItem";
import Tabs from "@theme/Tabs";

<Tabs
defaultValue="chr_auth_oidc"
values={[
{ label: "christiaangoossens/hass-oidc-auth", value: "chr_auth_oidc" },
{ label: "cavefire/hass-openid", value: "cav_openid" }
]}>
<TabItem value="cav_openid">

## authentik configuration

To support the integration of Home Assistant with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.

2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - Choose a **Provider Type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
        - Set a `Strict` redirect URI to `https://hass.company/auth/openid/callback`.
        - Select any available signing key (to use the RS256 `id_token_signing_alg`)
    - Configure Bindings (optional): you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Home Assistant configuration

1. Install hass-openid following the instructions at https://github.com/cavefire/hass-openid
2. To support the integration of Home Assistant with authentik, you'll need to update the `configuration.yaml` file of your Home Assistant deployment:

```yaml showLineNumbers title="/config/configuration.yaml"
openid:
    client_id: <authentik_client_ID>
    client_secret: <authentik_client_secret>
    configure_url: "https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration"
    scope: "openid profile email"
    username_field: "preferred_username"
    block_login: false
```

3. Restart Home Assistant

:::info
You must create OIDC users in Home Assistant before they can log in using OIDC.
:::

## Configuration verification

To verify the integration with Home Assistant, log out and attempt to log back in using the **OpenID/OAuth2 authentication** button. You should be redirected to the authentik login page. Once authenticated, you should be redirected to the Home Assistant dashboard.

## Resources

- [Integration repository](https://github.com/cavefire/hass-openid)

</TabItem>

<TabItem value="chr_auth_oidc">
## authentik configuration

To support the integration of Home Assistant with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.

2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - Choose a **Provider Type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
        - Set a `Strict` redirect URI to `https://hass.company/auth/oidc/callback`.
        - Select any available signing key (to use the RS256 `id_token_signing_alg`)
    - Configure Bindings (optional): you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Home Assistant configuration

:::info
This guide describes the UI configuration method, but you can also configure the integration using YAML.
:::

### UI configuration

1. Install [OpenID Connect/SSO Authentication](https://my.home-assistant.io/redirect/hacs_repository/?owner=christiaangoossens&repository=hass-oidc-auth&category=Integration) from HACS.
2. Log in to Home Assistant as an administrator and go to **Settings** > **Devices & Services**.
3. Click **Add Integration** and select **OpenID Connect/SSO Authentication**.
4. Select "Authentik" from the pre-configured providers.
5. Type in your discovery URL: `https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration`
6. On the next screen, Home Assistant will attempt to contact authentik on that URL to verify all the configuration. Continue to the next screen if everything looks okay.
7. You will be asked for both your **Client ID** and **Client Secret**.
8. Follow the rest of the configuration steps. You will be guided with on-screen prompts.

Finally, restart Home Assistant. You should now see a button to login with authentik. There is no need to create users manually, but you may want to temporarily enable 'User linking' to onboard existing Home Assistant users.

### YAML configuration

To configure the integration with YAML instead of the Home Assistant UI, add the following to your Home Assistant `configuration.yaml` file:

```yaml showLineNumbers title="/config/configuration.yaml"
auth_oidc:
    client_id: <authentik_client_id>
    client_secret: !secret authentik_client_secret
    discovery_url: "https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration"
```

Restart Home Assistant after changing `configuration.yaml`. If you configured the authentik provider as a public client, omit `client_secret`. For advanced options, such as role mapping, user linking, TLS settings, and public-client configuration, refer to the [hass-oidc-auth YAML configuration guide](https://github.com/christiaangoossens/hass-oidc-auth/blob/main/docs/configuration.md).

## Configuration verification

After configuration you will be taken to the integration settings screen where an entry named "Authentik" will be visible.

You should now automatically see the welcome screen upon opening your Home Assistant URL. On the welcome screen you can choose to either start login through SSO or to use an alternative login method, which will bring you back to the normal Home Assistant username/password login screen.

## Resources

- [hass-oidc-auth authentik configuration guide](https://github.com/christiaangoossens/hass-oidc-auth/blob/main/docs/provider-configurations/authentik.md)
- [YAML Configuration Guide (advanced users/features)](https://github.com/christiaangoossens/hass-oidc-auth/blob/main/docs/configuration.md)
- [Integration repository](https://github.com/christiaangoossens/hass-oidc-auth)

</TabItem>
</Tabs>
