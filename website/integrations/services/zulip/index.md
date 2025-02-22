---
title: Integrate with Zulip
sidebar_label: Zulip
support_level: community
---

## What is Zulip

> **Zulip**: Chat for distributed teams. Zulip combines the immediacy of real-time chat with an email threading model.
> With Zulip, you can catch up on important conversations while ignoring irrelevant ones.
>
> -- https://zulip.com

## Preparation

The following placeholders are used in this guide:

- `zulip.company` is the FQDN of the Zulip instance.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Zulip with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can create only an application, without a provider, by clicking **Create**.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **slug** as it will be required later.
- **Choose a Provider type**: select **SAML Provider** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Set the **ACS URL** to <kbd>https://<em>zulip.company</em>/complete/saml/</kbd>.
    - Set the **Issuer** to <kbd>https://<em>zulip.company</em></kbd>.
    - Set the **Service Provider Binding** to `Post`.
    - Under **Advanced protocol settings**, select an available signing certificate.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Zulip configuration

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
