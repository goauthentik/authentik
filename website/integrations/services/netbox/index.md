---
title: NetBox
---

<span class="badge badge--secondary">Support level: Community</span>

## What is NetBox

From https://github.com/netbox-community/netbox

:::note
NetBox is the leading solution for modeling and documenting modern networks.
:::

## Preparation

The following placeholders will be used:

-   `netbox.company` is the FQDN of the NetBox install.
-   `authentik.company` is the FQDN of the authentik install.

Create an application in authentik and note the slug you choose, as this will be used later. In the Admin Interface, go to Applications->Providers. Create a OAuth2/OpenID provider with the following parameters:

-   Client Type: `Confidential`
-   Redirect URIs: `https://netbox.company/oauth/complete/oidc/`
-   Scopes: OpenID, Email and Profile
-   Signing Key: Select any available key

Note the Client ID and Client Secret values. Create an application, using the provider you've created above.

## NetBox

:::caution
This setup was tested and developed with NetBox Docker. For a non-Docker installation, the Docker part must be disabled and the non-docker part must be used.
:::

The following Docker env vars are required for the configuration.

```env
# Enable python-social-auth
REMOTE_AUTH_ENABLED='true'
REMOTE_AUTH_BACKEND='social_core.backends.open_id_connect.OpenIdConnectAuth'

# python-social-auth config
SOCIAL_AUTH_OIDC_ENDPOINT='https://authentik.company/application/o/<Application slug>'
SOCIAL_AUTH_OIDC_KEY='<Client ID>'
SOCIAL_AUTH_OIDC_SECRET='<Client Secret>'
```

The Netbox configuration needs to be extended for this you can create a new file in the configuration folder, for example `authentik.py`.

```py
from os import environ

#############
# Docker
#############

# python-social-auth configuration
SOCIAL_AUTH_OIDC_ENDPOINT = environ.get('SOCIAL_AUTH_OIDC_ENDPOINT')
SOCIAL_AUTH_OIDC_KEY = environ.get('SOCIAL_AUTH_OIDC_KEY')
SOCIAL_AUTH_OIDC_SECRET = environ.get('SOCIAL_AUTH_OIDC_SECRET')


#############
# non Docker
#############

# NetBox settings
#REMOTE_AUTH_ENABLED = True
#REMOTE_AUTH_BACKEND = 'social_core.backends.open_id_connect.OpenIdConnectAuth'

# python-social-auth configuration
#SOCIAL_AUTH_OIDC_ENDPOINT = 'https://authentik.company/application/o/<Application
#SOCIAL_AUTH_OIDC_KEY = '<Client ID>'
#SOCIAL_AUTH_OIDC_SECRET = '<Client Secret>'
```
