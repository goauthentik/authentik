---
title: Integrate with Uptime Kuma
sidebar_label: Uptime Kuma
---

# Uptime Kuma

<span class="badge badge--secondary">Support level: Community</span>

## What is Uptime Kuma

> Uptime Kuma is an easy-to-use self-hosted monitoring tool.
>
> -- https://github.com/louislam/uptime-kuma

Uptime Kuma currently supports only a single user and no native SSO solution. To still use authentik, you can work with the Proxy Outpost and a Proxy Provider.

## Preparation

The following placeholders are used in this guide:

- `uptime-kuma.company` is the FQDN of the Uptime Kuma install.
- `authentik.company` is the FQDN of the authentik install.

Create an application in authentik. Create a Proxy provider with the following parameters:

- Internal host

    If Uptime Kuma is running in docker, and you're deploying the authentik proxy on the same host, set the value to `http://uptime-kuma:3001`, where uptime-kuma is the name of your container.

    If Uptime Kuma is running on a different server to where you are deploying the authentik proxy, set the value to `http://<Other Host>:3001`.

- External host

    `https://uptime-kuma.company`
    Set this to the external URL you will be accessing Uptime Kuma from.

- Skip path regex

    Add the following regex rules to keep the public status page accessible without authentication.

    ```
    ^/status/.*
    ^/assets/.*
    ^/api/push/.*
    ^/api/badge/.*
    ^/api/status-page/heartbeat/.*
    ^/icon.svg
    ^/upload/.*
    ```

    Alternatively, you can get even more specific by analyzing the requests for your status pages and modifying the regex rules above accordingly.  
     For example:

    ```
    ^/status/<slug>$
    ^/assets/.*
    ^/api/push/.*
    ^/api/badge/.*
    ^/api/status-page/heartbeat/<slug>$
    ^/upload/<file>$
    ```

To avoid that all users get admin access to Uptime Kuma create a group in authentik for the admin user. Next set in authentik for the application under `Policy / Group / User Bindings` a group binding with the group created above.

## Uptime Kuma

Disable auth from Uptime Kuma, go to `Settings` > `Advanced` > `Disable Auth`

To access the dashboard, open `https://uptime-kuma.company/dashboard`, this will start the login with authentik. You can also set this address as the Launch URL for the application.
