---
title: Integrate with NetBox
sidebar_label: NetBox
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is NetBox?

> NetBox is the world's most popular platform for understanding, operating, automating, and securing networks.
>
> -- https://netboxlabs.com/products/netbox/

## Preparation

The following placeholders are used in this guide:

- `netbox.company` is the FQDN of the NetBox installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of NetBox with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **Slug** value because it will be required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://netbox.company/oauth/complete/oidc/`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

### Configure NetBox entitlements _(optional)_

NetBox can create local groups from an OIDC `groups` claim by using a custom Social Auth pipeline. To control those groups with app-specific authentik grants, create an OAuth2 scope mapping that exposes application entitlements as the `groups` claim.

1. In authentik, navigate to **Customization** > **Property Mappings** and click **New Property Mapping**.
2. Select **OAuth2 Scope Mapping** and use the following values:
    - **Name**: `NetBox entitlements`
    - **Scope name**: `netbox`
    - **Expression**:

        ```python
        return {
            "name": request.user.name,
            "given_name": request.user.name,
            "preferred_username": request.user.username,
            "groups": [
                entitlement.name
                for entitlement in request.user.app_entitlements(provider.application)
            ],
        }
        ```

3. Open the NetBox provider that you created earlier and add `NetBox entitlements` to the selected **Scopes**.
4. Open the NetBox application and create the required **Application entitlements**. Use an entitlement named `superusers` for users that should receive NetBox superuser access through the optional pipeline below, and bind each entitlement to the users or groups that should receive it.

## NetBox configuration

NetBox supports SSO through the `python-social-auth` library. Configure the generic OpenID Connect backend, then restart NetBox so the configuration is loaded.

Use the authentik provider URL without `/.well-known/openid-configuration`. python-social-auth discovers the OpenID configuration from that endpoint.

### Configure NetBox Docker

Add the following environment variables to your NetBox Docker environment file:

```env title=".env"
REMOTE_AUTH_ENABLED=true
REMOTE_AUTH_BACKEND=social_core.backends.open_id_connect.OpenIdConnectAuth
SOCIAL_AUTH_OIDC_OIDC_ENDPOINT=https://authentik.company/application/o/<application_slug>/
SOCIAL_AUTH_OIDC_KEY=<Client ID from authentik>
SOCIAL_AUTH_OIDC_SECRET=<Client Secret from authentik>
SOCIAL_AUTH_OIDC_SCOPE=openid email profile
LOGOUT_REDIRECT_URL=https://authentik.company/application/o/<application_slug>/end-session/
```

If you configured the optional NetBox entitlements scope mapping, set `SOCIAL_AUTH_OIDC_SCOPE` to `openid email netbox`.

### Configure a non-Docker installation

Add the following settings to the NetBox configuration file:

```python title="/opt/netbox/netbox/netbox/configuration.py"
REMOTE_AUTH_ENABLED = True
REMOTE_AUTH_BACKEND = "social_core.backends.open_id_connect.OpenIdConnectAuth"

SOCIAL_AUTH_OIDC_OIDC_ENDPOINT = "https://authentik.company/application/o/<application_slug>/"
SOCIAL_AUTH_OIDC_KEY = "<Client ID from authentik>"
SOCIAL_AUTH_OIDC_SECRET = "<Client Secret from authentik>"
SOCIAL_AUTH_OIDC_SCOPE = ["openid", "email", "profile"]
LOGOUT_REDIRECT_URL = "https://authentik.company/application/o/<application_slug>/end-session/"
SOCIAL_AUTH_BACKEND_ATTRS = {
    "oidc": ("authentik", "login"),
}
```

If you configured the optional NetBox entitlements scope mapping, set `SOCIAL_AUTH_OIDC_SCOPE` to `["openid", "email", "netbox"]`.

### Sync groups and superuser status _(optional)_

To manage NetBox groups from authentik, create a custom Social Auth pipeline. The default authentik `profile` scope exposes authentik group names as the `groups` claim. If you configured the optional NetBox entitlements scope mapping, the `netbox` scope exposes application entitlement names instead.

Create `custom_pipeline.py` in the NetBox package directory. In the official NetBox Docker image, mount or add this file at `/opt/netbox/netbox/netbox/custom_pipeline.py`.

```python title="/opt/netbox/netbox/netbox/custom_pipeline.py"
from users.models import Group

SUPERUSER_GROUP = "superusers"


def _claim_groups(response):
    groups = response.get("groups", [])
    if isinstance(groups, str):
        return {groups}
    return set(groups)


def sync_groups(response, user, backend, *args, **kwargs):
    groups = [
        Group.objects.get_or_create(name=group_name)[0]
        for group_name in sorted(_claim_groups(response))
    ]
    user.groups.set(groups)


def set_superuser(response, user, backend, *args, **kwargs):
    user.is_superuser = SUPERUSER_GROUP in _claim_groups(response)
    user.save(update_fields=["is_superuser"])
```

Add the pipeline configuration to the NetBox configuration file. For NetBox Docker, place this setting in a Python configuration file that is loaded from the mounted `configuration/` directory, such as `configuration/authentik.py`.

```python title="/opt/netbox/netbox/netbox/configuration.py"
SOCIAL_AUTH_PIPELINE = (
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.social_user",
    "social_core.pipeline.user.get_username",
    "social_core.pipeline.user.create_user",
    "social_core.pipeline.social_auth.associate_user",
    "netbox.authentication.user_default_groups_handler",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
    "netbox.custom_pipeline.sync_groups",
    "netbox.custom_pipeline.set_superuser",
)
```

Restart NetBox after creating or updating the custom pipeline.

## Configuration verification

To confirm that authentik is properly configured with NetBox, open NetBox and select **authentik** on the login page. After a successful login, NetBox opens. If you enabled the optional group sync pipeline, verify that the user has the expected NetBox groups and superuser status.

## Resources

- [NetBox documentation - Authentication](https://netboxlabs.com/docs/netbox/administration/authentication/overview/)
- [NetBox documentation - Configuration](https://netboxlabs.com/docs/netbox/configuration/)
- [NetBox Docker - Configuration](https://github.com/netbox-community/netbox-docker/blob/release/configuration/configuration.py)
- [Python Social Auth - OIDC](https://python-social-auth.readthedocs.io/en/latest/backends/oidc.html)
