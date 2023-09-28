---
title: Ubuntu Landscape
---

<span class="badge badge--secondary">Support level: Community</span>

## What is Ubuntu Landscape

> Landscape is a systems management tool developed by Canonical. It can be run on-premises or in the cloud depending on the needs of the user. It is primarily designed for use with Ubuntu derivatives such as Desktop, Server, and Core.
>
> -- https://en.wikipedia.org/wiki/Landscape_(software)

:::caution
This requires authentik 0.10.3 or newer.
:::

## Preparation

The following placeholders will be used:

-   `landscape.company` is the FQDN of the Landscape server.
-   `authentik.company` is the FQDN of the authentik install.

Landscape uses the OpenID-Connect Protocol for single-sign on.

## authentik Setup

Create an OAuth2/OpenID-Connect Provider with the default settings. Set the Redirect URIs to `https://landscape.company/login/handle-openid`. Select all Managed Scopes.

Keep Note of the Client ID and the Client Secret.

Create an application and assign access policies to the application. Set the application's provider to the provider you've just created.

## Landscape Setup

On the Landscape Server, edit the file `/etc/landscape/service.conf` and add the following snippet under the `[landscape]` section:

```
oidc-issuer = https://authentik.company/application/o/<slug of the application you've created>/
oidc-client-id = <client ID of the provider you've created>
oidc-client-secret = <client Secret of the provider you've created>
```

Afterwards, run `sudo lsctl restart` to restart the Landscape services.

## Appendix

To make an OpenID-Connect User admin, you have to insert some rows into the database.

First login with your authentik user, and make sure the user is created successfully.

Run `sudo -u postgres psql landscape-standalone-main` on the Landscape server to open a PostgreSQL Prompt.
Then run `select * from person;` to get a list of all users. Take note of the ID given to your new user.

Run the following commands to make this user an administrator:

```sql
INSERT INTO person_account VALUES (<user id>, 1);
INSERT INTO person_access VALUES (<user id>, 1, 1);
```
