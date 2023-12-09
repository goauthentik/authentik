---
title: Immich
---

<span class="badge badge--secondary">Support level: Community</span>

## What is Immich

> Immich is a self-hosted backup solution for photos and videos on mobile devices
>
> -- https://immich.app/

## Preparation

The following placeholders will be used:

-   `immich.company` is the FQDN of the Immich install.
-   `192.168.0.2:2283` is the local IP address & port of the Immich install.
-   `authentik.company` is the FQDN of the authentik install.

## authentik Configuration

1. Create a new OAuth2/OpenID Provider
    - **Name**: Immich
	- **Authentication flow**: default-authentication-flow
	- **Authorization flow**: default-provider-authorization-explicit-consent
	- **Client type**: Conidential
	- **Client ID**: Either create your own Client ID or make a note of the auto-populated one
	- **Client Secret**: Either create your own Client Secret or make a note of the auto-populated one
	- **Redirect URIs/Origins (RegEx)**:
	  - app.immich:/
	  - http://192.168.0.2:2283/auth/login
	  - http://192.168.0.2:2283/user-settings
	  - https://immich.company/auth/login
	  - https://immich.company/user-settings
	- **Signing Key**: authentik Self-signed Certificate
    - Leave everything else as default
2. Open the new provider you've just created
3. Make a note of the **OpenID Configuration Issuer**

## Service Configuration

Immich documentation can be found here: https://immich.app/docs/administration/oauth

1. Go to Administration > Settings > OAuth Authentication
2. Configure Immich as follows:
    - **Issuer URL**: Populate this field with the `OpenID Configuration Issuer`
	- **Client ID**: Enter yout Client ID from authentik here
	- **Client Secret**: Enter yout Client Secret from authentik here
	- **Scope**: `openid email profile`
