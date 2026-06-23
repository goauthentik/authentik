---
title: Integrate with grommunio
sidebar_label: grommunio
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

<!-- spellchecker:ignore gromox -->

## What is grommunio?

> grommunio is an open-source groupware server and collaboration platform offering email, calendar, contacts, tasks, video conferencing, and file sync. It is fully compatible with Microsoft Outlook via MAPI/RPC, EWS, and ActiveSync.
>
> -- https://grommunio.com/

## Preparation

The following placeholders are used in this guide:

- `grommunio.company` is the FQDN of the grommunio installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To integrate authentik with grommunio, you will need to create an application and provider pair in authentik.

:::info Keycloak-compatible endpoints
grommunio Web uses Keycloak-compatible OIDC endpoints. Because authentik does not use Keycloak's `/realms/` endpoint structure, this guide configures an nginx bridge on the grommunio server.
:::

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name (e.g., `grommunio`), an optional group, and the policy engine mode. Note the application **Slug** because it will be required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name, the authorization flow to use, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://grommunio.company/web`.
        - Set **Signing Key** to an available RSA key.
        - Under **Advanced protocol settings**:
            - Add the `authentik default OAuth Mapping: OpenID 'offline_access'` scope to **Selected Scopes**.
    - **Configure Bindings** _(optional)_: create a binding to manage access.

3. Click **Submit** to save the new application and provider.

### Download certificate file

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click on the name of the provider that you created in the previous section.
3. Under **Related objects** > **Download signing certificate**, click on **Download**. This downloaded file is your certificate file and it will be required in the next section.

## grommunio configuration

### Configure gromox JWT verification

On the grommunio server, extract the public key from the certificate that you downloaded from authentik:

```bash
openssl x509 -pubkey -noout -in /path/to/authentik-signing-certificate.pem > /etc/gromox/bearer_pubkey
```

After creating the public key file, restart gromox:

```bash
systemctl restart gromox-http
```

### Create keycloak.json

grommunio Web uses a Keycloak-compatible OIDC configuration file at `/etc/gromox/keycloak.json`:

```json title="/etc/gromox/keycloak.json"
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

grommunio Web expects Keycloak-style OIDC endpoint paths under `/sso/realms/`. Add a custom nginx location file to proxy these to authentik.

```nginx title="/etc/grommunio-common/nginx/locations.d/sso-authentik.conf"
location = /sso/realms/grommunio/protocol/openid-connect/auth {
    return 302 https://authentik.company/application/o/authorize/$is_args$args;
}

location = /sso/realms/grommunio/protocol/openid-connect/token {
    proxy_pass https://authentik.company/application/o/token/;
    proxy_ssl_server_name on;
    proxy_set_header Host authentik.company;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location = /sso/realms/grommunio/protocol/openid-connect/token/introspect {
    proxy_pass https://authentik.company/application/o/introspect/;
    proxy_ssl_server_name on;
    proxy_set_header Host authentik.company;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location = /sso/realms/grommunio/protocol/openid-connect/userinfo {
    proxy_pass https://authentik.company/application/o/userinfo/;
    proxy_ssl_server_name on;
    proxy_set_header Host authentik.company;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location = /sso/realms/grommunio/protocol/openid-connect/logout {
    return 302 https://authentik.company/application/o/<application_slug>/end-session/$is_args$args;
}
```

Then reload nginx:

```bash
nginx -t && nginx -s reload
```

### Patch class.keycloak.php

grommunio Web's OIDC client does not request the `email` or `offline_access` scopes by default. Without these scopes, grommunio cannot map the authentik user from the access token or refresh the session after login.

Open `/usr/share/php-mapi/class.keycloak.php` and update the two scope strings from `openid` to `openid email offline_access`.

There should be one occurrence in the authorization URL builder and one in the token request. Example diff:

```diff title="/usr/share/php-mapi/class.keycloak.php"
- $params['scope'] = 'openid';
+ $params['scope'] = 'openid email offline_access';

- return $this->realm_url . '/protocol/openid-connect/auth?scope=openid&client_id=' . urlencode((string) $this->client_id) . '&state=' . urlencode($uuid) . '&redirect_uri=' . urlencode($redirect_url) . '&response_type=code';
+ return $this->realm_url . '/protocol/openid-connect/auth?scope=openid%20email%20offline_access&client_id=' . urlencode((string) $this->client_id) . '&state=' . urlencode($uuid) . '&redirect_uri=' . urlencode($redirect_url) . '&response_type=code';
```

After saving, reload PHP-FPM:

```bash
systemctl reload php-fpm
```

## Configuration verification

Log out of grommunio Web completely, then open grommunio Web. You should be redirected to the authentik login page. After authenticating, you will be returned to grommunio Web and logged in automatically.

To verify single logout, click the logout button in grommunio Web. You should be redirected to the authentik session invalidation flow.

## Resources

- [grommunio Web - login template](https://github.com/grommunio/grommunio-web/blob/master/server/includes/templates/login.php)
- [grommunio Web - Keycloak authentication flow](https://github.com/grommunio/grommunio-web/blob/master/server/includes/core/class.webappauthentication.php)
- [grommunio mapi-header-php - Keycloak client](https://github.com/grommunio/mapi-header-php/blob/master/class.keycloak.php)
- [Gromox - bearer token verification](https://github.com/grommunio/gromox/blob/master/exch/authmgr.cpp)
