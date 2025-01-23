---
title: Integrate with pgAdmin
sidebar_label: pgAdmin
---

# pgAdmin

<span class="badge badge--secondary">Support level: Community</span>

## What is pgAdmin

> pgAdmin is a management tool for PostgreSQL and derivative relational databases such as EnterpriseDB's EDB Advanced Server. It may be run either as a web or desktop application.
>
> -- https://www.pgadmin.org/

:::note
This is based on authentik 2024.12.2 and pgAdmin4 8.14
:::

## Preparation

The following placeholders are used in this guide:

- `pgadmin.company` is the FQDN of pgAdmin installation.
- `authentik.company` is the FQDN of authentik installation.

:::note
This documentation lists only the settings that have been changed from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

# authentik configuration

1. From the Admin interface, navigate to **Applications** -> **Applications**.
2. Use the wizard to create a new application and provider. During this process:
    - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to `https://pgadmin.company/oauth2/authorize`.
    - Select any available signing key.

## pgAdmin OAuth Configuration

To configure OAuth in pgAdmin, you can either use the `config_local.py` file or set environment variables if you are deploying pgAdmin in a containerized setup.

### Using `config_local.py`

1. Locate or create the `config_local.py` file in the `/pgadmin4/` directory.

    - If the file does not exist, create it manually.

2. Add the following configuration settings to `config_local.py`:

    ```python
    AUTHENTICATION_SOURCES = ['oauth2', 'internal']
    OAUTH2_AUTO_CREATE_USER = True
    OAUTH2_CONFIG = [{
        'OAUTH2_NAME': 'authentik',
        'OAUTH2_DISPLAY_NAME': 'authentik',
        'OAUTH2_CLIENT_ID': '<Client ID from authentik>',
        'OAUTH2_CLIENT_SECRET': '<Client secret from authentik>',
        'OAUTH2_TOKEN_URL': 'https://authentik.company/application/o/token/',
        'OAUTH2_AUTHORIZATION_URL': 'https://authentik.company/application/o/authorize/',
        'OAUTH2_API_BASE_URL': 'https://authentik.company/',
        'OAUTH2_USERINFO_ENDPOINT': 'https://authentik.company/application/o/userinfo/',
        'OAUTH2_SERVER_METADATA_URL': 'https://authentik.company/application/o/<App Slug>/.well-known/openid-configuration',
        'OAUTH2_SCOPE': 'openid email profile',
        'OAUTH2_ICON': '<Fontawesome icon key (e.g., fa-key)>',
        'OAUTH2_BUTTON_COLOR': '<Hexadecimal color code for the login button>'
    }]
    ```

3. Save the file and restart pgAdmin for the changes to take effect.

    :::note
    You must restart pgAdmin every time you make changes to `config_local.py`.
    :::

### Using Environment Variables for Containerized Deployments

For deployments using Docker or Kubernetes, you can configure OAuth using the following environment variables:

1. Set these environment variables in your container:

```bash
PGADMIN_CONFIG_AUTHENTICATION_SOURCES="['oauth2', 'internal']"
PGADMIN_CONFIG_OAUTH2_AUTO_CREATE_USER=True
PGADMIN_CONFIG_OAUTH2_CONFIG="[{'OAUTH2_NAME':'authentik','OAUTH2_DISPLAY_NAME':'Login with authentik','OAUTH2_CLIENT_ID':'<Client ID from authentik>','OAUTH2_CLIENT_SECRET':'<Client secret from authentik>','OAUTH2_TOKEN_URL':'https://authentik.company/application/o/token/','OAUTH2_AUTHORIZATION_URL':'https://authentik.company/application/o/authorize/','OAUTH2_API_BASE_URL':'https://authentik.company/','OAUTH2_USERINFO_ENDPOINT':'https://authentik.company/application/o/userinfo/','OAUTH2_SERVER_METADATA_URL':'https://authentik.company/application/o/<App Slug>/.well-known/openid-configuration','OAUTH2_SCOPE':'openid email profile','OAUTH2_ICON':'<Fontawesome icon key (e.g., fa-key)>','OAUTH2_BUTTON_COLOR':'<Hexadecimal color code for the login button>'}]"
```

### General Notes

- To **only allow OAuth2 login**, set:

    ```python
    AUTHENTICATION_SOURCES = ['oauth2']
    ```

    Ensure that you promote at least one user to an admin before disabling the internal authentication.

- To **disable automatic user creation**, set:
    ```python
    OAUTH2_AUTO_CREATE_USER = False
    ```
    Setting this value to `False` disables automatic user creation. This ensures that only the first signed-in user is registered.

## Configuration verification

To confirm that authentik is properly configured with pgAdmin, log out and log back in via authentik. A new button should have appeared on the login page.
