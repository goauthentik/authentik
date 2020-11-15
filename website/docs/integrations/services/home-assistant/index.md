---
title: Home-Assistant
---

## What is Home-Assistant

From https://www.home-assistant.io/

:::note
Open source home automation that puts local control and privacy first. Powered by a worldwide community of tinkerers and DIY enthusiasts. Perfect to run on a Raspberry Pi or a local server.
:::

## Preparation

The following placeholders will be used:

- `hass.company` is the FQDN of the Home-Assistant install.
- `passbook.company` is the FQDN of the passbook install.

:::note
This setup uses https://github.com/BeryJu/hass-auth-header and the passbook proxy for authentication. When this [PR](https://github.com/home-assistant/core/pull/32926) is merged, this will no longer be necessary.
:::

## Home-Assistant

This guide requires https://github.com/BeryJu/hass-auth-header, which can be installed as described in the Readme.

Afterwards, make sure the `trusted_proxies` setting contains the IP(s) of the Host(s) passbook is running on.

With the default Header of `X-Forwarded-Preferred-Username` matching is done on a username basis, so your Name in Home-Assistant and your username in passbook have to match.

If this is not the case, you can simply add an additional header for your user, which contains the Home-Assistant Name and authenticate based on that.

For example add this to your user's properties and set the Header to `X-pb-hass-user`.

```yaml
additionalHeaders:
  X-pb-hass-user: some other name
```

## passbook

Create a Proxy Provider with the following values

- Internal host

    If Home-Assistant is running in docker, and you're deploying the passbook proxy on the same host, set the value to `http://homeassistant:8123`, where Home-Assistant is the name of your container.

    If Home-Assistant is running on a different server than where you are deploying the passbook proxy, set the value to `http://hass.company:8123`.

- External host

    Set this to the external URL you will be accessing Home-Assistant from.

Create an application in passbook and select the provider you've created above.

## Deployment

Create an outpost deployment for the provider you've created above, as described [here](../../../outposts/outposts.md). Deploy this Outpost either on the same host or a different host that can access Home-Assistant.

The outpost will connect to passbook and configure itself.
