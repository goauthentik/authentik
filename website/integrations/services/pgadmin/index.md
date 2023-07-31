---
title: pgAdmin
---

<span class="badge badge--secondary">Support level: Community</span>

## What is pgAdmin

> pgAdmin is a management tool for PostgreSQL and derivative relational databases such as EnterpriseDB's EDB Advanced Server. It may be run either as a web or desktop application.
>
> -- https://www.pgadmin.org/

:::note
This is based on authentik 2022.3.3 and pgAdmin4 6.19
:::

## Preparation

The following placeholders will be used:

-   `pgadmin.company` is the FQDN of pgAdmin.
-   `authentik.company` is the FQDN of authentik.

### Step 1: Create authentik Provider

In authentik, under _Providers_, create an _OAuth2/OpenID Provider_ with these settings:

**Provider Settings**

-   Name: pgAdmin
-   Client ID: Copy and Save this for Later
-   Client Secret: Copy and Save this for later
-   Redirect URIs/Origins: `http://pgadmin.company/oauth2/authorize`
-   Signing Key: Select any available key

### Step 2: Create authentik Application

In authentik, create an application which uses this provider. Optionally apply access restrictions to the application using policy bindings.

-   Name: pgAdmin
-   Slug: pgadmin
-   Provider: pgAdmin
-   Launch URL: https://pgadmin.company

### Step 3: Configure pgAdmin

All settings for OAuth in pgAdmin are configured in the `config_local.py` file. This file can usually be found in the path `/pgadmin4/config_local.py`

:::note
More information on that file can be found in the official pgAdmin [documentation](https://www.pgadmin.org/docs/pgadmin4/development/config_py.html)
:::

Copy the following code into the `config_local.py` file and replace all placeholders and FQDN placeholders
:::note
If the `config_local.py` file does not exist, it needs to be created in the `/pgadmin4/` directory.
:::

```py
AUTHENTICATION_SOURCES = ['oauth2', 'internal']
OAUTH2_AUTO_CREATE_USER = True
OAUTH2_CONFIG = [{
	'OAUTH2_NAME' : 'authentik',
	'OAUTH2_DISPLAY_NAME' : '<display-name>',
	'OAUTH2_CLIENT_ID' : '<client-id>',
	'OAUTH2_CLIENT_SECRET' : '<client-secret>',
	'OAUTH2_TOKEN_URL' : 'https://authentik.company/application/o/token/',
	'OAUTH2_AUTHORIZATION_URL' : 'https://authentik.company/application/o/authorize/',
	'OAUTH2_API_BASE_URL' : 'https://authentik.company/',
	'OAUTH2_USERINFO_ENDPOINT' : 'https://authentik.company/application/o/userinfo/',
	'OAUTH2_SERVER_METADATA_URL' : 'https://authentik.company/application/o/<app-slug>/.well-known/openid-configuration',
	'OAUTH2_SCOPE' : 'openid email profile',
	'OAUTH2_ICON' : '<fontawesome-icon>',
	'OAUTH2_BUTTON_COLOR' : '<button-color>'
}]
```

In the code above the following placeholders have been used:

-   `<display-name>`: The name that is displayed on the Login Button
-   `<client-id>`: The Client ID from step 1
-   `<client-secret>`: The Client Secret from step 1
-   `<app-slug>`: The App Slug from step 2, it should be `pgadmin` if you did not change it
-   `<fontawesome-icon>`: An icon name from [fontawesome](https://fontawesome.com). Only brand icons seem to be supported. This icon is displayed in front of the `<display-name>`. E.g.: _fa-github_.
-   `<button-color>`: Sets the color of the Login Button. Should be in Hex format, E.g.: _#fd4b2d_

:::note
To only allow authentication via authentik set `AUTHENTICATION_SOURCES` to _['oauth2']_. This should **only** be done once at least one user registered via authentik has been made an admin in pgAdmin.
:::

:::note
To disable user creation on pgAdmin, set `OAUTH2_AUTO_CREATE_USER` to _False_
:::

Finally, restart pgAdmin to apply the changes.

:::note
pgAdmin needs to be restarted **every** time changes to `config_local.py` are made
:::
