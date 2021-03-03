---
title: Sonarr
---

# Sonarr Integration

:::note
These instructions apply to all projects in the \*arr Family. If you use multiple of these projects, you can assign them to the same Outpost.
:::

## What is Sonarr

From https://github.com/Sonarr/Sonarr

:::note
Sonarr is a PVR for Usenet and BitTorrent users. It can monitor multiple RSS feeds for new episodes of your favorite shows and will grab, sort and rename them. It can also be configured to automatically upgrade the quality of files already downloaded when a better quality format becomes available.
:::

## Preparation

The following placeholders will be used:

- `sonarr.company` is the FQDN of the Sonarr install.
- `authentik.company` is the FQDN of the authentik install.

Create a Proxy Provider with the following values

- Internal host

    If Sonarr is running in docker, and you're deploying the authentik proxy on the same host, set the value to `http://sonarr:8989`, where sonarr is the name of your container.

    If Sonarr is running on a different server than where you are deploying the authentik proxy, set the value to `http://sonarr.company:8989`.

- External host

    Set this to the external URL you will be accessing Sonarr from.

Create an application in authentik and select the provider you've created above.

## Deployment

Create an outpost deployment for the provider you've created above, as described [here](../../../outposts/outposts.md). Deploy this Outpost either on the same host or a different host that can access Sonarr.

The outpost will connect to authentik and configure itself.
