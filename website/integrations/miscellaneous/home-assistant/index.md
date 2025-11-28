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

It is possible to configure Home Assistant to use OIDC or a proxy provider for authentication. Below are the steps to configure each method.

import TabItem from "@theme/TabItem";
import Tabs from "@theme/Tabs";

<Tabs
defaultValue="oidc"
values={[
{ label: "OIDC", value: "oidc" },
{ label: "Proxy Provider", value: "proxy" }
]}

>   <TabItem value="oidc">

## authentik configuration

To support the integration of Home Assistant with authentik you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID** as the provider type.
    - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
        - **Signing Key**: Select any available signing key.
        - **Redirect URIs**:
            - Strict: `http://hass.company:8123/auth/openid/callback`

    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

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
  <TabItem value="proxy">

:::caution
Using a proxy provider might produce CSRF errors. This is caused by a technology that Home Assistant uses and not authentik. For more information see [this GitHub issue](https://github.com/goauthentik/authentik/issues/884#issuecomment-851542477).
:::

:::caution
Only prefixes starting with `/auth` need to be proxied (excluding prefixes starting with `/auth/token`). See [this GitHub issue](https://github.com/BeryJu/hass-auth-header/issues/212). This can be configured in the reverse proxy (e.g. nginx, Traefik) or in authentik Provider's **Unauthorized Paths**.
:::

## authentik configuration

To support the integration of Home Assistant using `hass-auth-headers` with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **Proxy** as the provider type.
        - **External Host**: Set this to the external URL you will be accessing Home Assistant from.
        - **Internal Host**: `http://hass.company:8123`

    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

4. Create an outpost deployment for the provider you've created above, as described [here](https://docs.goauthentik.io/docs/add-secure-apps/outposts/). Deploy this Outpost either on the same host or a different host that can access Home Assistant. The outpost will connect to authentik and configure itself.

## Home Assistant configuration

1. Configure [trusted_proxies](https://www.home-assistant.io/integrations/http/#trusted_proxies) for the HTTP integration with the IP(s) of the Host(s) authentik is running on.
2. If you don't already have it set up, https://github.com/BeryJu/hass-auth-header, using the installation guide.
3. There are two ways to configure the custom component:

### Match on user's authentik username

To match on the user's authentik username, use the following configuration:

    ```yaml
    auth_header:
        username_header: X-authentik-username
    ```

### Associate existing Home Assistant username

Alternatively, you can associate an existing Home Assistant username to an authentik username.

1. Within authentik, navigate to **Directory** > **Users**.
2. Select **Edit** for the user then add the following configuration to the **Attributes** section. Be sure to replace `hassusername` with the Home Assistant username.

:::info
This configuration adds an extra header for the authentik user, containing the Home Assistant username, which allows Home Assistant to authenticate the user accordingly.
:::

    ```yaml
    additionalHeaders:
        X-ak-hass-user: hassusername
    ```

3. Then configure the Home Assistant custom component to use this header:

    ```yaml
    auth_header:
        username_header: X-ak-hass-user
    ```

  </TabItem>
</Tabs>
