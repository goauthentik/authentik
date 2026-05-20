---
title: Integrate with OpenCloud
sidebar_label: OpenCloud
support_level: community
---

## What is OpenCloud?

> OpenCloud is an open-source content collaboration platform for storing, syncing, and sharing files, built on the Infinite Scale (oCIS) architecture.
>
> -- https://opencloud.eu

## Preparation

The following placeholders are used in this guide:

- `opencloud.company` is the FQDN of the OpenCloud installation.
- `authentik.company` is the FQDN of the authentik installation.
- `opencloud` is the slug of the authentik application.

This guide covers the [`opencloud-compose`](https://github.com/opencloud-eu/opencloud-compose) Docker deployment. OpenCloud authenticates only through OpenID Connect.

## authentik configuration

1. Log in to authentik as an administrator and open the Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application**.
    - **Application**: provide a name and note the **slug**.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect**.
    - **Configure the Provider**:
        - **Client type**: `Public`
        - **Client ID**: `web`
        - **Redirect URIs**: add the following entries (each row's first dropdown is the matching mode, the second is the type):
            - Type **Authorization**, **Strict**: `https://opencloud.company/oidc-callback.html`
            - Type **Authorization**, **Strict**: `https://opencloud.company/oidc-silent-redirect.html`
            - Type **Post Logout**, **Strict**: `https://opencloud.company/`
        - **Signing Key**: select any available key.
        - **Scopes**: `openid`, `profile`, `email`.
        - **Invalidation flow** (under **Flow settings**): `default-invalidation-flow` (**Default - Invalidation flow**). The default provider invalidation flow does not end the authentik session, which causes OpenCloud to immediately log back in after logout. If you want to use `default-provider-invalidation-flow` and keep your authentik session on logout, remove the Post Logout Redirect URI that you set above.
3. Click **Submit**.

## OpenCloud configuration

In the `opencloud-compose` project, enable the external IdP overlay in `COMPOSE_FILE`. This replaces OpenCloud's built-in IdP, so login goes through authentik only.

```bash
COMPOSE_FILE=docker-compose.yml:idm/external-idp.yml:custom/authentik-roles.yml
```

Set the OIDC values in `.env`:

```bash
OC_DOMAIN=opencloud.company
IDP_DOMAIN=authentik.company
IDP_ISSUER_URL=https://authentik.company/application/o/<slug>/
OC_OIDC_CLIENT_ID=web
OC_OIDC_CLIENT_SCOPES=openid profile email
WEBFINGER_WEB_OIDC_CLIENT_ID=web
WEBFINGER_WEB_OIDC_CLIENT_SCOPES=openid profile email
```

:::info
`WEBFINGER_WEB_OIDC_CLIENT_ID` is required — the Web UI reads its client ID from WebFinger, and login will not start if it is empty.
:::

Create `custom/authentik-roles.yml` to assign every user the default role:

```yaml
---
services:
    opencloud:
        environment:
            PROXY_ROLE_ASSIGNMENT_DRIVER: "default"
            GRAPH_ASSIGN_DEFAULT_USER_ROLE: "true"
```

Recreate the stack:

```bash
docker compose up -d
```

## Verification

Open `https://opencloud.company` in a new browser window. You are redirected to authentik to log in, and after authenticating you are returned to OpenCloud.

## Resources

- [OpenCloud documentation](https://docs.opencloud.eu/)
- [opencloud-compose](https://github.com/opencloud-eu/opencloud-compose)
