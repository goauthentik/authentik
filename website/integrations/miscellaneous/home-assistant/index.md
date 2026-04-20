---
title: Integrate with Home Assistant
sidebar_label: Home Assistant
support_level: community
---

## What is Home Assistant

> Open source home automation that puts local control and privacy first. Powered by a worldwide community of tinkerers and DIY enthusiasts. Perfect to run on a Raspberry Pi or a local server.
>
> -- https://www.home-assistant.io/

:::info
To integrate Home Assistant with authentik, a custom integration needs to be installed in Home Assistant.
:::

## Preparation

The following placeholders are used in this guide:

- `hass.company` is the FQDN of the Home Assistant installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## Configuration methods

The community has developed multiple custom integrations to link authentik to Home Assistant:

- https://github.com/cavefire/hass-openid
- https://github.com/christiaangoossens/hass-oidc-auth

Both are explained in their own tabs below. You should evaluate which integration is the best fit for you carefully before continuing with this guide. Both use the **OpenID Connect** standard to link authentik to Home Assistant securely, but each have their own values and features.

import TabItem from "@theme/TabItem";
import Tabs from "@theme/Tabs";

<Tabs
defaultValue="oidc"
values={[
{ label: "OIDC (christiaangoossens/hass-oidc-auth)", value: "chr_auth_oidc" },
{ label: "OIDC (cavefire/hass-openid)", value: "cav_openid" }
]}>
<TabItem value="chr_auth_oidc">
## authentik configuration

1. Log in to authentik as an administrator and open the authentik Admin interface.

2. Navigate to **Applications > Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

 -   **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
 -   Choose a **Provider Type**: select **OAuth2/OpenID Connect** as the provider type.
 -   **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
        - Set a `Strict` redirect URI to `https://hass.company/auth/oidc/callback`.
        - Select any available signing key (to use the RS256 `id_token_signing_alg`)
  -  Configure Bindings (optional): you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

## Home Assistant configuration
:::tip
You can find a more detailed configuration guide, with picture guidance, at [https://github.com/christiaangoossens/hass-oidc-auth/blob/main/docs/provider-configurations/authentik.md](https://github.com/christiaangoossens/hass-oidc-auth/blob/main/docs/provider-configurations/authentik.md).
:::

:::info
This guide describes the UI configuration method, but you can also configure the integration using YAML.
:::

1. Install 'OpenID Configuration' from the HACS store.
2. Open Home Assistant and go to **Settings -> Devices & Services**.
3. Click Add Integration and select **OpenID Connect/SSO Authentication**.
4. Select "Authentik" from the pre-configured providers.
5. Type in your discovery URL: `https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration`
6. On the next screen, Home Assistant will attempt to contact authentik on that URL to verify all the configuration. Continue to the next screen if everything looks okay.
7. You will be asked for both your **Client ID** and **Client Secret**.
8. Follow the rest of the configuration steps. You will be guided with on-screen prompts.

Finally, restart Home Assistant. You should now see a button to login with authentik. There is no need to create users manually, but you may want to temporarily enable 'User linking' to onboard existing Home Assistant users.


</TabItem>
<TabItem value="cav_openid">
## authentik configuration

To support the integration of Home Assistant with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID** as the provider type.
    - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
        - **Signing Key**: Select any available signing key.
        - **Redirect URIs**:
            - Strict: `http://hass.company:8123/auth/openid/callback`

    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

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

</TabItem>
</Tabs>
