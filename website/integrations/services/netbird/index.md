---
title: Integrate with NetBird
sidebar_label: NetBird
---

# Integrate with NetBird

<span class="badge badge--secondary">Support level: Community</span>

## What is NetBird?

> NetBird is an open source, zero trust, networking platform that allows you to create secure private networks for your organization or home.
>
> -- https://netbird.io

## Preparation

The following placeholders are used in this guide:

- `netbird.company` is the FQDN of the NetBird installation.
- `authentik.company` is the FQDN of the authentik installation.

## authentik configuration

### Provider & application configuration

1. Access the **Admin Interface** of your authentik installation.
2. Create a new **OAuth2 / OpenID Provider**.
3. Ensure the **Client Type** is set to `Public`.
4. Note the generated **Client ID** and **Client Secret**.
5. In the provider settings, add the following redirect URLs under **Redirect URIs/Origins**:
    - Strict; `https://netbird.company`
    - Regex; `https://netbird.company/.*`
    - Strict; `http://localhost:53000`
6. Under **Signing Key**, select an available key. By default, the authentik self-signed certificate is available.
7. Under **Advanced Protocol Settings**, set the **Access Code Validity** to `minutes=10` and set the **Subject Mode** to `Based on the User's ID`.
8. Click **Finish** to save the provider configuration.
9. Create a new application associated with this provider.

### Service account setup

1. Access the **Admin Interface** of your authentik install once more.
2. Navigate to **Directory** -> **Users**, and click **Create a service account**.
3. Set the username to `NetBird` and disable the **Create group** option.
4. Take note of the generated password.

### Adding the service account to the administrator group

1. Under **Directory** -> **Groups**, select the `authentik Default Admins` group and switch to the **Users** tab near the top of the page.
2. Click **Add existing user** and then select your NetBird service account.

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
