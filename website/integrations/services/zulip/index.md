---
title: Zulip
---

:::info
This integration describes how to use Zulip's SAML support with Authentik.
:::

## What is Zulip

From https://zulip.com

:::note
**Zulip**: Chat for distributed teams. Zulip combines the immediacy of real-time chat with an email threading model.
With Zulip, you can catch up on important conversations while ignoring irrelevant ones. 
:::

## Preperation

The following placeholders will be used:

- `authentik.company` is the FQDN of the authentik install.
- `<application slug>` is the slug you have set for this application (i.e 'zulip')

Create the application and saml provider on Authentik, making sure the Service Provider Binding
is set to `Post`.

## Zulip Configuration

:::note
Zulip is a Django application and is configured using `/etc/zulip/settings.py`. Only settings that differ
from the defaults are displayed below. Please make sure you have the latest `settings.py` file as more settings 
might have been added to defaults since you installed Zulip.
:::

Uncomment `zproject.backends.SAMLAuthBackend` inside the `AUTHENTICATION_BACKENDS` parameter to enable SAML support
and fill in the following required configuration.

```
SOCIAL_AUTH_SAML_ORG_INFO = {
    "en-US": {
        "displayname": "Authentik Zulip",
        "name": "zulip",
        "url": "{}{}".format("https://", EXTERNAL_HOST),
    },
}

SOCIAL_AUTH_SAML_ENABLED_IDPS: Dict[str, Any] = {
    # idp identifier and settings
    "authentik": {
       
	    # KEEP OTHER SETTINGS AS DEFAULT OR CONFIGURE THEM ACCORDING TO YOUR PREFERENCES
        "entity_id": "https://authentik.company",
        "url": "https://${authentik.company}/application/saml/<application slug>/sso/binding/redirect/",
        "display_name": "Authentik SAML",
    },
}

```

Place the certificate you associated with the SAML provider in Authentik inside the `/etc/zulip/saml/idps` directory. 
The certificate file name must match the idp identifier name you set in the configuration (i.e. authentik.crt).

:::note
Remember to restart Zulip.
:::
## Additional Resources

Please refer to the following for further information:

- https://zulip.com/
- https://zulip.readthedocs.io
- https://chat.zulip.org/ (Official public Zulip Chat instance)
