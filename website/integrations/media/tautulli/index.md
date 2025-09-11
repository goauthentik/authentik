---
title: Integrate with Tautulli
sidebar_label: Tautulli
support_level: community
---

## What is Tautulli

> Tautulli is a 3rd party application that you can run alongside your Plex Media Server to monitor activity and track various statistics. Most importantly, these statistics include what has been watched, who watched it, when and where they watched it, and how it was watched. The only thing missing is "why they watched it", but who am I to question your 42 plays of Frozen. All statistics are presented in a nice and clean interface with many tables and graphs, which makes it easy to brag about your server to everyone else.
>
> -- https://tautulli.com/

## Preparation

The following placeholders are used in this guide:

- `tautulli.company` is the FQDN of the Tautulli installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Tautulli with authentik, you need to create an application/provider pair in authentik.

Because Tautulli requires valid HTTP Basic credentials, you must save your HTTP Basic Credentials in authentik. The recommended way to do this is to create a Group. Name the group "Tautulli Users", for example. For this group, add the following attributes:

```yaml
tautulli_user: username
tautulli_password: password
```

Add all Tautulli users to the Group. You should also create a Group Membership Policy to limit access to the application.

## Tautulli configuration

- Internal host

    If Tautulli is running in docker, and you're deploying the authentik proxy on the same host, set the value to `http://tautulli:3579`, where tautulli is the name of your container.

    If Tautulli is running on a different server to where you are deploying the authentik proxy, set the value to `http://tautulli.company:3579`.

- External host

    Set this to the external URL you will be accessing Tautulli from.

    Basic authentication settings have been removed from the UI and are now available in the `config.ini` file. For basic auth to work, do the following:

1. Close Tautulli.

2. Set the following in the config file:

```yaml
http_basic_auth = 1
http_hash_password = 0
http_hashed_password = 1
http_password = `<enter your password>`
```

3. Save the changes and then restart Tautulli.

4. Afterwards, you need to deploy an Outpost in front of Tautulli, as described [here](https://docs.goauthentik.io/docs/add-secure-apps/outposts/).
   Note: You can use the embedded outpost and simply add Tatulli to the list of applications to use.

## Configuration verification

To confirm that authentik is properly configured with Tautulli, log out and log back in via authentik (you can use private browsing mode to validate) and navigate to Tautulli. You should bypass the login prompt if setup correctly.
