---
title: Zulip
---

<span class="badge badge--secondary">Support level: Community</span>

## What is Zulip

> Zulip is an open-source team communication platform that combines the immediacy of chat with the organization of threaded conversations.
>
> -- https://zulip.com

## Preparation

The following placeholders will be used:

-   `authentik.company` is the FQDN of the authentik install.
-   `zulip.company` is the FQDN of the Zulip instance.

## authentik configuration

Create a new application and note the **slug**, as this will be used later. Create a SAML provider with the following parameters:

-   **ACS URL**: `https://zulip.company/complete/saml/`
-   **Issuer**: `https://authentik.company`
-   **Service Provider Binding**: **Post**
-   **Signing Keypair**: Select any certificate you have.
-   **Property mappings**: Select all Managed mappings.

## Zulip configuration

Zulip is a Django application and is configured using `/etc/zulip/settings.py`. Only settings that differ
from the defaults are displayed below. Please make sure you have the latest `/etc/zulip/settings.py` file as more settings
might have been added to defaults since you installed Zulip.

Uncomment `zproject.backends.SAMLAuthBackend` inside the `AUTHENTICATION_BACKENDS` parameter to enable SAML support
and fill in the following required configuration.

```
SOCIAL_AUTH_SAML_ORG_INFO = {
"en-US": {
"displayname": "authentik Zulip",
"name": "zulip",
"url": "{}{}".format("https://", EXTERNAL_HOST),
},
}

SOCIAL_AUTH_SAML_ENABLED_IDPS: Dict[str, Any] = {
# idp identifier and settings
"authentik": {
    "entity_id": "https://authentik.company",
    "url": "https://authentik.company/application/saml/<em>application-slug</em>/sso/binding/redirect/",
    "display_name": "authentik SAML",
},
}
```
Place the certificate you associated with the SAML provider in authentik inside the `/etc/zulip/saml/idps` directory.
The certificate file name must match the idp identifier name you set in the configuration (i.e. `authentik.crt`).

:::note
Remember to restart Zulip.
:::