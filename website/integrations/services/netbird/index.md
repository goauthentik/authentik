---
title: Integrate with NetBird
sidebar_label: NetBird
support_level: community
---

## What is NetBird?

> NetBird is an open source, zero trust, networking platform that allows you to create secure private networks for your organization or home.
>
> -- https://netbird.io

## Preparation

The following placeholders are used in this guide:

- `netbird.company` is the FQDN of the NetBird installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of NetBird with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can create only an application, without a provider, by clicking **Create**.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Add two `Strict` redirect URIs and set them to <kbd>http://localhost:53000</kbd> and <kbd>https://<em>netbird.company</em></kbd>. Then, add a `Regex` redirect URI and set it to <kbd>https://<em>netbird.company</em>/.\*</kbd>.
    - Select any available signing key.
    - Under **Advanced Protocol Settings**, set **Access Code Validity** to `minutes=10`, then set **Subject Mode** to be `Based on the User's ID`.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

### Set up a service account

1. Log into authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Directory** > **Users**, and click **Create a service account**.
3. Set the **Username** to `NetBird` and disable the **Create group** option. Click **Create** and take note of the **password**.

### Make the service account an administrator

NetBird requires the service account to have full administrative access to the authentik instance. Follow these steps to make it an administrator.

1. Log into authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Directory** > **Groups**, and click **`authentik Admins`**.
3. On the top of the group configuration page, switch to the **Users** tab near the top of the page, then click **Add existing user**, and select the service account you just created.

## NetBird configuration

To configure NetBird to use authentik, add the following values to your `setup.env` file:

```
NETBIRD_AUTH_OIDC_CONFIGURATION_ENDPOINT="https://authentik.company/application/o/netbird/.well-known/openid-configuration"
NETBIRD_USE_AUTH0=false
NETBIRD_AUTH_CLIENT_ID="<Your Client ID>"
NETBIRD_AUTH_SUPPORTED_SCOPES="openid profile email offline_access api"
NETBIRD_AUTH_AUDIENCE="<Your Client Secret>"
NETBIRD_AUTH_DEVICE_AUTH_CLIENT_ID="<Your Client ID>"
NETBIRD_AUTH_DEVICE_AUTH_AUDIENCE="<Your Client ID>"
NETBIRD_MGMT_IDP="authentik"
NETBIRD_IDP_MGMT_CLIENT_ID="<Your Client ID>"
NETBIRD_IDP_MGMT_EXTRA_USERNAME="Netbird"
NETBIRD_IDP_MGMT_EXTRA_PASSWORD="<Your Service Account password>"
```

After making these changes, restart your Docker containers to apply the new configuration.

Once completed, NetBird should be successfully configured to use authentik as its Single Sign-On provider.
