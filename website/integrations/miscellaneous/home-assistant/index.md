---
title: Integrate with Home Assistant
sidebar_label: Home Assistant
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";
import TabItem from "@theme/TabItem";
import Tabs from "@theme/Tabs";

<!-- spellchecker:ignore christiaangoossens hass -->

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

Home Assistant does not include built-in support for SSO protocols. This guide covers two community-maintained OpenID Connect integrations:

- [christiaangoossens/hass-oidc-auth](https://github.com/christiaangoossens/hass-oidc-auth)
- [cavefire/hass-openid](https://github.com/cavefire/hass-openid)

Choose one integration before continuing, then use the matching tab in the authentik and Home Assistant configuration sections.

## authentik configuration

<RedirectURI20265Note />

To support the integration of Home Assistant with authentik, you need to create an application/provider pair in authentik.

<Tabs
defaultValue="hass_oidc_auth"
values={[
{ label: "christiaangoossens/hass-oidc-auth", value: "hass_oidc_auth" },
{ label: "cavefire/hass-openid", value: "hass_openid" },
]}>
<TabItem value="hass_oidc_auth">

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the application **Slug** because you will use it later as `<application_slug>`.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://hass.company/auth/oidc/callback`.
        - Set **Signing Key** to any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

</TabItem>
<TabItem value="hass_openid">

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **Slug** value because it will be required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://hass.company/auth/openid/callback`.
        - Set **Signing Key** to any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

</TabItem>
</Tabs>

## Home Assistant configuration

<Tabs
defaultValue="hass_oidc_auth"
values={[
{ label: "christiaangoossens/hass-oidc-auth", value: "hass_oidc_auth" },
{ label: "cavefire/hass-openid", value: "hass_openid" },
]}>
<TabItem value="hass_oidc_auth">

### UI configuration

1. Install [OpenID Connect/SSO Authentication](https://my.home-assistant.io/redirect/hacs_repository/?owner=christiaangoossens&repository=hass-oidc-auth&category=Integration) from HACS.
2. Restart Home Assistant if HACS asks you to do so.
3. Log in to Home Assistant as an administrator and go to **Settings** > **Devices & Services**.
4. Click **Add Integration** and select **OpenID Connect/SSO Authentication**.
5. Select the authentik provider from the pre-configured providers.
6. Set **Discovery URL** to `https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration`.
7. Continue after Home Assistant successfully validates the discovery URL.
8. Enter the **Client ID** and **Client Secret** from authentik.
9. Configure the group and user-linking options for your Home Assistant deployment, then finish the setup.

:::warning Temporary user linking only
Only enable automatic user linking while migrating existing Home Assistant users to OIDC. Disable it again after the users are linked.
:::

### YAML configuration

To configure the integration with YAML instead of the Home Assistant UI, add the following to your Home Assistant configuration:

```yaml showLineNumbers title="/config/configuration.yaml"
auth_oidc:
    client_id: <Client ID from authentik>
    client_secret: !secret authentik_client_secret
    discovery_url: "https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration"
```

Restart Home Assistant after changing `configuration.yaml`. For advanced options, such as role mapping, user linking, TLS settings, and public-client configuration, refer to the hass-oidc-auth YAML configuration guide linked in the resources section.

</TabItem>
<TabItem value="hass_openid">

### UI configuration

1. Install [OpenID / OAuth2 authentication](https://my.home-assistant.io/redirect/hacs_repository/?category=integration&repository=hass-openid&owner=cavefire) from HACS.
2. Restart Home Assistant if HACS asks you to do so.
3. Log in to Home Assistant as an administrator and go to **Settings** > **Devices & Services**.
4. Click **Add Integration** and select **OpenID / OAuth2 authentication**.
5. Select **Use configure URL**.
6. Set **Configure URL** to `https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration`.
7. Review the discovered provider endpoints and continue.
8. Enter the **Client ID** and **Client secret** from authentik.
9. Configure the identity mapping and advanced options for your Home Assistant deployment, then finish the setup.

:::warning Test before blocking other login methods
Only enable **Block other login methods** after you have confirmed that OpenID login works, otherwise you can lock yourself out of Home Assistant.
:::

### Legacy YAML configuration

The Home Assistant UI config flow is the recommended setup method for hass-openid. If you still use the legacy YAML configuration, add the following to your Home Assistant configuration:

```yaml showLineNumbers title="/config/configuration.yaml"
openid:
    client_id: <Client ID from authentik>
    client_secret: <Client Secret from authentik>
    configure_url: "https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration"
```

Restart Home Assistant after changing `configuration.yaml`.

</TabItem>
</Tabs>

## Configuration verification

To confirm that authentik is properly configured with Home Assistant, open Home Assistant and start an SSO login with the integration you configured. You should be redirected to authentik and then back to Home Assistant after successful authentication.

## Resources

- [hass-oidc-auth authentik configuration guide](https://github.com/christiaangoossens/hass-oidc-auth/blob/main/docs/provider-configurations/authentik.md)
- [hass-oidc-auth YAML configuration guide](https://github.com/christiaangoossens/hass-oidc-auth/blob/main/docs/configuration.md)
- [hass-openid setup guide](https://github.com/cavefire/hass-openid/blob/main/README.md)
- [hass-openid legacy YAML configuration guide](https://github.com/cavefire/hass-openid/blob/main/LEGACY_CONFIGURATION.md)
