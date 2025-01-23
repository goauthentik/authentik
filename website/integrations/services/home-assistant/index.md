---
title: Integrate with Home Assistant
sidebar_label: Home Assistant
---

# Integrate with Home Assistant

<span class="badge badge--secondary">Support level: Community</span>

## What is Home Assistant

> Open source home automation that puts local control and privacy first. Powered by a worldwide community of tinkerers and DIY enthusiasts. Perfect to run on a Raspberry Pi or a local server.
>
> -- https://www.home-assistant.io/

:::caution
You might run into CSRF errors, this is caused by a technology Home-assistant uses and not authentik, see [this GitHub issue](https://github.com/goauthentik/authentik/issues/884#issuecomment-851542477).
:::
:::caution
Only prefixes starting with `/auth` need to be proxied (excluding prefixes starting with `/auth/token`), see [this GitHub issue](https://github.com/BeryJu/hass-auth-header/issues/212). This can be configured in the reverse proxy (e.g. nginx, Traefik) or in authentik Provider's **Unauthorized Paths**.
:::
:::note
For Home Assistant to work with authentik, a custom integration needs to be installed for Home Assistant.
:::

## Preparation

The following placeholders are used in this guide:

- `hass.company` is the FQDN of the Home Assistant installation.
- `authentik.company` is the FQDN of the authentik installation.

## authentik configuration

1. Create a **Proxy Provider** under **Applications** > **Providers** using the following settings:

    - **Name**: Home Assistant
    - **Authentication flow**: default-authentication-flow
    - **Authorization flow**: default-provider-authorization-explicit-consent
    - **External Host**: Set this to the external URL you will be accessing Home Assistant from
    - **Internal Host**: `http://hass.company:8123`

2. Create an **Application** under **Applications** > **Applications** using the following settings:

    - **Name**: Home Assistant
    - **Slug**: homeassistant
    - **Provider**: Home Assistant (the provider you created in step 1)

3. Create an outpost deployment for the provider you've created above, as described [here](https://docs.goauthentik.io/docs/add-secure-apps/outposts/index.md). Deploy this Outpost either on the same host or a different host that can access Home Assistant. The outpost will connect to authentik and configure itself.

## Home Assistant configuration

1. Configure [trusted_proxies](https://www.home-assistant.io/integrations/http/#trusted_proxies) for the HTTP integration with the IP(s) of the Host(s) authentik is running on.
2. If you don't already have it set up, https://github.com/BeryJu/hass-auth-header, using the installation guide.
3. There are two ways to configure the custom component.
    1. To match on the user's authentik username, use the following configuration:
        ```yaml
        auth_header:
            username_header: X-authentik-username
        ```
    2. Alternatively, you can associate an existing Home Assistant username to an authentik username.
        1. Within authentik, navigate to **Directory** > **Users**.
        2. Select **Edit** for the user then add the following configuration to the **Attributes** section. Be sure to replace `hassusername` with the Home Assistant username.
           :::note
           This configuration will add an additional header for the authentik user which will contain the Home Assistant username and allow Home Assistant to authenticate based on that.
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
