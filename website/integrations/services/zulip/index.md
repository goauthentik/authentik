---
title: Integrate with Zulip
sidebar_label: Zulip
---

# Integrate with Zulip

<span class="badge badge--secondary">Support level: Community</span>

## What is Zulip

> Zulip is an open-source team chat application that organizes conversations into topic-based streams, enabling more structured and efficient communication compared to traditional linear chat platforms.
>
> -- https://zulip.com

## Preparation

The following placeholders are used in this guide:

- `zulip.company` is the FQDN of the Zulip instance.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

Create an application in authentik and note the slug, as this will be used later. Create a SAML provider with the following parameters:

- ACS URL: `https://zulip.company/complete/saml/`
- Issuer: `https://authentik.company`
- Service Provider Binding: `Post`
- Signing Keypair: Select any certificate you have.
- Property mappings: Select all Managed mappings.

## Zulip Configuration

Zulip is a Django application and is configured using `/etc/zulip/settings.py`. Only settings that differ
from the defaults are displayed below. Please make sure you have the latest `settings.py` file as more settings
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

	    # KEEP OTHER SETTINGS AS DEFAULT OR CONFIGURE THEM ACCORDING TO YOUR PREFERENCES
        "entity_id": "https://authentik.company",
        "url": "https://authentik.company/application/saml/<application slug>/sso/binding/redirect/",
        "display_name": "authentik SAML",
    },
}

```

Place the certificate you associated with the SAML provider in authentik inside the `/etc/zulip/saml/idps` directory.
The certificate file name must match the idp identifier name you set in the configuration (i.e. authentik.crt).

:::note
Remember to restart Zulip.
:::

## Additional Resources

Please refer to the following for further information:

- https://zulip.com/
- https://zulip.readthedocs.io
- https://chat.zulip.org/ (Official public Zulip Chat instance)
