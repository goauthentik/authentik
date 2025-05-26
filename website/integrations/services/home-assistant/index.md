---
title: Integrate with Home Assistant
sidebar_label: Home Assistant
support_level: community
---

## What is Home Assistant

> Open source home automation that puts local control and privacy first. Powered by a worldwide community of tinkerers and DIY enthusiasts. Perfect to run on a Raspberry Pi or a local server.
>
> -- https://www.home-assistant.io/

:::note
For Home Assistant to work with authentik, a custom integration needs to be installed for Home Assistant.
:::

## Preparation

The following placeholders are used in this guide:

- `hass.company` is the FQDN of the Home Assistant installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::


## Using OAuth2 / OpenID

### authentik configuration

1. Create a **OAuth2/OpenID Provider** under **Applications** > **Providers**:
    - Note the **Client ID** and **Client Secret** values because they will be required later.
    - Set a `Regex` redirect URI to `^(http:\/\/hass\.company\:8123)\/auth\/openid\/callback.*`. (Note the `\` in front of every `.`, `/` and `:`. Check you regex [here](https://regex101.com)
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

2. Create an **Application** under **Applications** > **Applications** using the following settings:

    - **Name**: Home Assistant
    - **Slug**: homeassistant
    - **Provider**: Home Assistant (the provider you created in step 1)

### Home Assistant configuration

1. Follow the installation guide on [https://github.com/cavefire/hass-openid](https://github.com/cavefire/hass-openid?tab=readme-ov-file#installation).
2. Using a file editor or ssh, edit the file `configuration.yaml` in your homeassistant's `config` by appending the following:
    ```yaml
    openid:
        client_id: <Client ID from Step 1>
        client_secret: <Client Secret from Step 1>
        authorize_url: "https://authentik.company/application/o/authorize/"
        token_url: "https://authentik.company/application/o/token/"
        user_info_url: "https://authentik.company/application/o/userinfo/"
        scope: "openid profile email"
        username_field: "preferred_username"
    ```
3. Restart Home Assistant

The login page now has a button called "OpenID/OAuth2 authentication". Click it to redirect you to authentik to sign in.
Make sure the user account has been created in Homeassistant, since this integration does not create the users for you.


## Using a proxy

:::caution
You might run into CSRF errors, this is caused by a technology Home-assistant uses and not authentik, see [this GitHub issue](https://github.com/goauthentik/authentik/issues/884#issuecomment-851542477).
:::
:::caution
Only prefixes starting with `/auth` need to be proxied (excluding prefixes starting with `/auth/token`), see [this GitHub issue](https://github.com/BeryJu/hass-auth-header/issues/212). This can be configured in the reverse proxy (e.g. nginx, Traefik) or in authentik Provider's **Unauthorized Paths**.
:::

### authentik configuration

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

3. Create an outpost deployment for the provider you've created above, as described [here](https://docs.goauthentik.io/docs/add-secure-apps/outposts/). Deploy this Outpost either on the same host or a different host that can access Home Assistant. The outpost will connect to authentik and configure itself.

### Home Assistant configuration

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
