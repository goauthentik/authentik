---
title: Integrate with pgAdmin
sidebar_label: pgAdmin
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is pgAdmin?

> pgAdmin is a management tool for PostgreSQL and derivative relational databases such as EnterpriseDB's EDB Advanced Server. It may be run either as a web or desktop application.
>
> -- https://www.pgadmin.org/

## Preparation

The following placeholders are used in this guide:

- `pgadmin.company` is the FQDN of the pgAdmin installation.
- `authentik.company` is the FQDN of the authentik installation.

This guide assumes that pgAdmin is running in Server mode.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of pgAdmin with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **Slug** because it will be required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - **Protocol Settings**:
            - **Redirect URI**:
                - `Strict` `Authorization`: `https://pgadmin.company/oauth2/authorize`
            - **Signing Key**: select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## pgAdmin configuration

To configure OIDC in pgAdmin, use either `config_local.py` or environment variables if you are deploying pgAdmin in a containerized setup.

### Configure with `config_local.py`

1. Locate or create the `config_local.py` file in the `/pgadmin4/` directory.
2. Add the following configuration to the file:

    ```py title="/pgadmin4/config_local.py"
    AUTHENTICATION_SOURCES = ["oauth2", "internal"]
    OAUTH2_CONFIG = [
        {
            "OAUTH2_NAME": "authentik",
            "OAUTH2_DISPLAY_NAME": "authentik",
            "OAUTH2_CLIENT_ID": "<Client ID from authentik>",
            "OAUTH2_CLIENT_SECRET": "<Client Secret from authentik>",
            "OAUTH2_SERVER_METADATA_URL": "https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration",
            "OAUTH2_SCOPE": "openid email profile",
        }
    ]
    ```

3. Save the file and restart pgAdmin.

### Configure with environment variables

For containerized deployments, set these environment variables:

```env title=".env"
PGADMIN_CONFIG_AUTHENTICATION_SOURCES="['oauth2', 'internal']"
PGADMIN_CONFIG_OAUTH2_CONFIG="[{'OAUTH2_NAME':'authentik','OAUTH2_DISPLAY_NAME':'authentik','OAUTH2_CLIENT_ID':'<Client ID from authentik>','OAUTH2_CLIENT_SECRET':'<Client Secret from authentik>','OAUTH2_SERVER_METADATA_URL':'https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration','OAUTH2_SCOPE':'openid email profile'}]"
```

Restart the pgAdmin container after changing the environment variables.

### Adjust login policy _(optional)_

To only allow authentik login, remove `internal` from `AUTHENTICATION_SOURCES` after at least one OAuth2 user has been promoted to the pgAdmin **Administrator** role:

```py title="/pgadmin4/config_local.py"
AUTHENTICATION_SOURCES = ["oauth2"]
```

To require pgAdmin administrators to create OAuth2 users manually before those users can sign in, disable automatic user creation:

```py title="/pgadmin4/config_local.py"
OAUTH2_AUTO_CREATE_USER = False
```

## Configuration verification

To confirm that authentik is properly configured with pgAdmin, open pgAdmin and click the **authentik** button on the login page. After signing in through authentik, you should be redirected back to pgAdmin.

## Resources

- [pgAdmin documentation - Enabling OAUTH2 and OIDC Authentication](https://www.pgadmin.org/docs/pgadmin4/latest/oauth2.html)
- [pgAdmin documentation - Container Deployment](https://www.pgadmin.org/docs/pgadmin4/latest/container_deployment.html)
- [pgAdmin documentation - User Management](https://www.pgadmin.org/docs/pgadmin4/latest/user_management.html)
