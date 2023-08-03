---
title: Home-Assistant
---

<span class="badge badge--secondary">Support level: Community</span>

## What is Home-Assistant

> Open source home automation that puts local control and privacy first. Powered by a worldwide community of tinkerers and DIY enthusiasts. Perfect to run on a Raspberry Pi or a local server.
>
> -- https://www.home-assistant.io/

:::caution
You might run into CSRF errors, this is caused by a technology Home-assistant uses and not authentik, see [this GitHub issue](https://github.com/goauthentik/authentik/issues/884#issuecomment-851542477).
:::

## Preparation

The following placeholders will be used:

-   `hass.company` is the FQDN of the Home-Assistant install.
-   `authentik.company` is the FQDN of the authentik install.

## Home-Assistant

This guide requires https://github.com/BeryJu/hass-auth-header, which can be installed as described in the Readme.

Afterwards, make sure the `trusted_proxies` setting contains the IP(s) of the Host(s) authentik is running on.

Use this configuration to match on the user's authentik username.

```yaml
auth_header:
    username_header: X-authentik-username
```

If this is not the case, you can simply add an additional header for your user, which contains the Home-Assistant Name and authenticate based on that.

For example add this to your user's properties and set the Header to `X-ak-hass-user`.

```yaml
additionalHeaders:
    X-ak-hass-user: some other name
```

## authentik

Create a Proxy Provider with the following values

-   Internal host

    If Home-Assistant is running in docker, and you're deploying the authentik proxy on the same host, set the value to `http://homeassistant:8123`, where Home-Assistant is the name of your container.

    If Home-Assistant is running on a different server than where you are deploying the authentik proxy, set the value to `http://hass.company:8123`.

-   External host

    Set this to the external URL you will be accessing Home-Assistant from.

Create an application in authentik and select the provider you've created above.

## Deployment

Create an outpost deployment for the provider you've created above, as described [here](../../../docs/outposts/). Deploy this Outpost either on the same host or a different host that can access Home-Assistant.

The outpost will connect to authentik and configure itself.
