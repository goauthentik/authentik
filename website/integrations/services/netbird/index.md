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
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Under **Protocol Settings**:
        - Note the **Client ID**, and **slug** values because they will be required later.
        - Set **Client type** to `Public`.
        - Add two `Strict` redirect URIs: `http://localhost:53000` and `https://<netbird.company>`.
        - Add a `Regex` redirect: `https://<netbird.company>.*`.
        - Select any available signing key.
    - Under **Advanced Protocol Settings**:
        - Set **Access Code Validity** to `minutes=10`.
        - Set **Subject Mode** to be `Based on the User's ID`.
        - Add the `authentik default OAuth Mapping: OpenID 'offline_access'` and `authentik default OAuth Mapping: authentik API access` scopes to **Selected Scopes**.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

:::warning
It is important to set a signing key to secure the provider because this is a `Public` client.
:::

:::note
If an access group is created for the Netbird application, the Netbird service account must be included in the group. Otherwise you will see a 401 error after login.
:::

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

### Create and apply a device token authentication flow

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Flows & Stages** > **Flows** and click **Create**.
3. Set the following required configurations:
    - **Name**: provide a name (e.g. `default-device-code-flow`)
    - **Title**: provide a title (e.g. `Device code flow`)
    - **Slug**: provide a slug (e.g `default-device-code-flow`)
    - **Designation**: `Stage Configuration`
    - **Authentication**: `Require authentication`
4. Click **Create**.
5. Navigate to **System** > **Brands** and click the **Edit** icon on the default brand.
6. Set **Default code flow** to the newly created device code flow and click **Update**.

## NetBird configuration

To configure NetBird to use authentik, add the following environment variables to your NetBird deployment:

```yaml showLineNumbers
NETBIRD_AUTH_OIDC_CONFIGURATION_ENDPOINT="https://authentik.company/application/o/<application slug>/.well-known/openid-configuration"
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

Restart the NetBird service for the changes to take effect. If using Docker, redeploy the NetBird container for the changes to take effect.

## Configuration verification

To confirm that authentik is properly configured with NetBird, log out and log back in via authentik.

## Troubleshooting

If using a reverse proxy to access NetBird it's possible to get stuck in a loop where the `/peers` URL will reload. To resolve this set the following variables in your NetBird `setup.env` file:

```yaml title="setup.env"
NETBIRD_MGMT_API_PORT=443
NETBIRD_SIGNAL_PORT=443
```

Run the `configure.sh` script for the change to take effect.
