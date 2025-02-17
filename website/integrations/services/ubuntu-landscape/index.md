---
title: Integrate with Ubuntu Landscape
sidebar_label: Ubuntu Landscape
support_level: community
---

## What is Ubuntu Landscape

> Landscape is a systems management tool developed by Canonical. It can be run on-premises or in the cloud depending on the needs of the user. It is primarily designed for use with Ubuntu derivatives such as Desktop, Server, and Core.
>
> -- https://en.wikipedia.org/wiki/Landscape_(software)

:::caution
This requires authentik 0.10.3 or newer.
:::

## Preparation

The following placeholders are used in this guide:

- `landscape.company` is the FQDN of the Landscape server.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

Landscape uses the OpenID-Connect Protocol for single-sign on.

## authentik configuration

To support the integration of Landscape with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can create only an application, without a provider, by clicking **Create.)**

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to <kbd>https://<em>landscape.company</em>/login/handle-openid</kbd>.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Landscape configuration

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
