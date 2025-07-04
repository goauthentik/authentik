---
title: Integrate with Seafile
sidebar_label: Seafile
support_level: community
---

## What is Seafile

> Seafile is an open-source, cross-platform file-hosting software system. Files are stored on a central server and can be synchronized with personal computers and mobile devices through apps. Files on the Seafile server can also be accessed directly via the server's web interface.
> -- https://seafile.com

## Preparation

The following placeholders are used in this guide:

- `seafile.company` is the FQDN of the Seafile installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Seafile with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select OAuth2/OpenID Connect as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Set a `Strict` redirect URI to `https://seafile.company/oauth/callback`.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Seafile configuration

To support the integration of Seafile with authentik, you'll need to update the `seahub_settings.py` file of your Seafile deployment (The location may vary depending on your installation and deployment methods):

```yaml showLineNumbers title="seahub_settings.py"
CSRF_TRUSTED_ORIGINS = ["https://seafile.company"]

ENABLE_OAUTH = True

# Automatically creates a user in Seafile when they log in for the first time. Defaults to True.
OAUTH_CREATE_UNKNOWN_USER = True

# Automatically activate Seafile users when they log in for the first time. Defaults to True.
OAUTH_ACTIVATE_USER_AFTER_CREATION = True

OAUTH_CLIENT_ID = "<client_id_from_authentik>"
OAUTH_CLIENT_SECRET = "<client_secret_from_authentik>"

OAUTH_REDIRECT_URL = 'https://seafile.company/oauth/callback/'

OAUTH_PROVIDER = 'authentik'

OAUTH_PROVIDER_DOMAIN = 'https:/authentik.company'
OAUTH_AUTHORIZATION_URL = 'https://authentik.company/application/o/authorize/'
OAUTH_TOKEN_URL = 'https://authentik.company/application/o/token/'
OAUTH_USER_INFO_URL = 'https://authentik.company/application/o/userinfo/'
OAUTH_SCOPE = [ "openid", "profile", "email",]

OAUTH_ATTRIBUTE_MAP = {
    "email": (True, "email"),
    "name": (False, "name"),
}
```

## Configuration verification

To confirm that authentik is properly configured with Seafile, log out of Seafile. Then, navigate to the Seafile login page, and click **Log in using SSO**. You should be redirected to authentik to log in, and if the process is successful, you'll be taken to the Seafile dashboard.

## Resources

- [Seafile Oauth authentication documentation](https://manual.seafile.com/13.0/config/oauth/)
- [Seafile `seahub_settings.py` documentation](https://manual.seafile.com/13.0/config/seahub_settings_py/)
