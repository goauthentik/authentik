---
title: Integrate with grommunio
sidebar_label: grommunio
support_level: community
---

## What is grommunio?

> grommunio is an open-source groupware server and collaboration platform offering email, calendar, contacts, tasks, video conferencing, and file sync. It is fully compatible with Microsoft Outlook via MAPI/RPC, EWS, and ActiveSync.
>
> -- https://grommunio.com/

:::info
This guide requires grommunio-web 2023.10 or later. The integration uses grommunio-web's built-in Keycloak/OIDC compatibility layer, so no additional plugins are needed.
:::

## Preparation

The following placeholders are used in this guide:

- `grommunio.company` is the FQDN of the grommunio installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To integrate authentik with grommunio, you will need to create an application and provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name (e.g., `grommunio`), an optional group, and the policy engine mode.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name, the authorization flow to use, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Set a `Strict` redirect URI to `https://grommunio.company/web`.
        - Set **Signing Key** to an available RS256 or ES256 key.
        - Under **Advanced Protocol Settings**:
            - Set **Subject mode** to `Based on the User's Email`.
            - Add the `authentik default OAuth Mapping: OpenID 'offline_access'` scope to **Selected Scopes**.
    - **Configure Bindings** _(optional)_: create a binding to manage access.

3. Click **Create Application** to save the new application and provider.

### Download certificate file

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click on the name of the provider that you created in the previous section.
3. Under **Related objects** > **Download signing certificate**, click on **Download**. This downloaded file is your certificate file and it will be required in the next section.

## grommunio configuration

### Configure gromox JWT verification

On the grommunio server, edit your `/etc/gromox/http.cfg` file to include the contents of your authentik signging certificate:

```bash title="/etc/gromox/http.cfg"
# Add the PEM-encoded public key (replace newlines with \n):
bearer_pubkey = -----BEGIN CERTIFICATE-----\nMIID...
```

After editing, restart gromox:

```bash
systemctl restart gromox-http
```

### Create keycloak.json

grommunio-web uses a Keycloak-compatible OIDC configuration file at `/etc/grommunio-common/nginx/keycloak.json`:

```json
{
    "realm": "grommunio",
    "auth-server-url": "https://grommunio.company/sso/",
    "ssl-required": "external",
    "resource": "<Client ID from authentik>",
    "credentials": {
        "secret": "<Client Secret from authentik>"
    }
}
```

### Add the nginx SSO bridge

grommunio-web expects Keycloak-style OIDC endpoint paths under `/sso/realms/`. Add a custom nginx location file to proxy these to authentik.

Create `/etc/grommunio-common/nginx/locations.d/sso-authentik.conf`:

```nginx
location ~* ^/sso/realms/grommunio/protocol/openid-connect/auth {
    return 302 https://authentik.company/application/o/authorize/$is_args$args;
}

location = /sso/realms/grommunio/protocol/openid-connect/token {
    proxy_pass https://authentik.company/application/o/token/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location = /sso/realms/grommunio/protocol/openid-connect/userinfo {
    proxy_pass https://authentik.company/application/o/userinfo/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location = /sso/realms/grommunio/protocol/openid-connect/logout {
    return 302 https://authentik.company/application/o/grommunio/end-session/$is_args$args;
}
```

Then reload nginx:

```bash
nginx -t && nginx -s reload
```

### Patch class.keycloak.php

grommunio-web's OIDC client does not request the `offline_access` scope by default, which means authentik will not return a `refresh_token`, causing a redirect loop after login. Apply the following fix:

Open `/usr/share/grommunio-web/lib/class.keycloak.php` and find the two occurrences of `openid email` in the scope strings, then change them to `openid email offline_access`.

There should be one occurrence in the authorization URL builder and one in the token request. Example diff:

```diff
- $scope = 'openid email';
+ $scope = 'openid email offline_access';
```

After saving, reload PHP-FPM:

```bash
systemctl reload php-fpm
```

## Configuration verification

Log out of grommunio-web completely, then navigate to `https://grommunio.company/web`. You should be redirected to the authentik login page. After authenticating, you will be returned to grommunio-web and logged in automatically.

To verify single logout, click the logout button in grommunio-web — you should be redirected to the authentik session invalidation flow on `authentik.company`.
