---
title: Sonarr
---

<span class="badge badge--secondary">Support level: Community</span>

:::note
These instructions apply to all projects in the \*arr Family. If you use multiple of these projects, you can assign them to the same Outpost.
:::

## What is Sonarr

> Sonarr is a PVR for Usenet and BitTorrent users. It can monitor multiple RSS feeds for new episodes of your favorite shows and will grab, sort and rename them. It can also be configured to automatically upgrade the quality of files already downloaded when a better quality format becomes available.
>
> -- https://github.com/Sonarr/Sonarr

## Preparation

The following placeholders will be used:

-   `sonarr.company` is the FQDN of the Sonarr install.
-   `authentik.company` is the FQDN of the authentik install.

Create a Proxy Provider with the following values

-   Internal host

    If Sonarr is running in docker, and you're deploying the authentik proxy on the same host, set the value to `http://sonarr:8989`, where sonarr is the name of your container.

    If Sonarr is running on a different server than where you are deploying the authentik proxy, set the value to `http://sonarr.company:8989`.

-   External host

    Set this to the external URL you will be accessing Sonarr from.

Create an application in authentik and select the provider you've created above.

## Deployment

Create an outpost deployment for the provider you've created above, as described [here](../../../docs/outposts/). Deploy this Outpost either on the same host or a different host that can access Sonarr.

The outpost will connect to authentik and configure itself.

## Authentication Setup

Because Sonarr can use HTTP Basic credentials, you can save your HTTP Basic Credentials in authentik. The recommended way to do this is to create a Group. Name the group "Sonarr Users", for example. For this group, add the following attributes:

```yaml
sonarr_user: username
sonarr_password: password
```

Add all Sonarr users to the Group. You should also create a Group Membership Policy to limit access to the application.

Enable the `Use Basic Authentication` option. Set and `HTTP-Basic Username` and `HTTP-Basic Password` to `sonarr_user` and `sonarr_password` respectively. These values can be chosen freely, `sonarr_` is just used as a prefix for clarity.

## Reverse Proxy Setup

Finally, in your reverse proxy setup for Sonarr, replace the current value with your Authentik Server
