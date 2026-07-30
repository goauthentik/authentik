---
title: Integrate with Seafile
sidebar_label: Seafile
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Seafile?

> Seafile is an open-source, cross-platform file-hosting software system. Files are stored on a central server and can be synchronized with personal computers and mobile devices through apps. Files on the Seafile server can also be accessed directly via the server's web interface.
>
> -- https://seafile.com/

## Preparation

The following placeholders are used in this guide:

- `seafile.company` is the FQDN of the Seafile installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Seafile with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://seafile.company/oauth/callback/`.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## Seafile configuration

To support the integration of Seafile with authentik, update the `seahub_settings.py` file of your Seafile deployment. The location of this file can vary depending on your installation method.

```py showLineNumbers title="seahub_settings.py"
CSRF_TRUSTED_ORIGINS = ["https://seafile.company"]

ENABLE_OAUTH = True

OAUTH_CLIENT_ID = "<Client ID from authentik>"
OAUTH_CLIENT_SECRET = "<Client Secret from authentik>"

OAUTH_REDIRECT_URL = "https://seafile.company/oauth/callback/"
OAUTH_PROVIDER = "authentik"
OAUTH_PROVIDER_DOMAIN = "authentik"
OAUTH_AUTHORIZATION_URL = "https://authentik.company/application/o/authorize/"
OAUTH_TOKEN_URL = "https://authentik.company/application/o/token/"
OAUTH_USER_INFO_URL = "https://authentik.company/application/o/userinfo/"
OAUTH_SCOPE = ["openid", "profile", "email"]

OAUTH_ATTRIBUTE_MAP = {
    "sub": (True, "uid"),
    "name": (False, "name"),
    "email": (False, "contact_email"),
}
```

Restart Seahub after updating `seahub_settings.py`.

### Single sign-on behavior _(optional)_

To automatically redirect users to the Seafile OAuth login flow, add the following setting:

```py showLineNumbers title="seahub_settings.py"
LOGIN_URL = "https://seafile.company/oauth/login/"
```

If users sign in from Seafile desktop clients, enable single sign-on in the system browser:

```py showLineNumbers title="seahub_settings.py"
CLIENT_SSO_VIA_LOCAL_BROWSER = True
```

## Configuration verification

To confirm that authentik is properly configured with Seafile, log out of Seafile. Then, open Seafile and click **Single Sign-On**. You should be redirected to authentik to log in, and if the process is successful, you'll be taken to the Seafile dashboard.

## Resources

- [Seafile OAuth authentication documentation](https://manual.seafile.com/13.0/config/oauth/)
- [Seafile `seahub_settings.py` documentation](https://manual.seafile.com/13.0/config/seahub_settings_py/)
