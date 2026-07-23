---
title: Integrate with Zulip
sidebar_label: Zulip
support_level: community
---

import SAMLProvider20265Warning from "../../\_saml-provider-2026-5-warning.mdx";

## What is Zulip?

> Zulip is an open-source team chat application that organizes conversations into topic-based streams, enabling more structured and efficient communication compared to traditional linear chat platforms.
>
> -- https://zulip.com

## Preparation

The following placeholders are used in this guide:

- `zulip.company` is the FQDN of the Zulip instance.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Zulip with authentik, you need to create SAML property mappings and an application/provider pair in authentik.

### Create property mappings

Zulip expects SAML attributes for the user's email address and name. Create SAML provider property mappings that send those values with the attribute names used in the Zulip configuration.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings**, click **Create**, select **SAML Provider Property Mapping**, and then click **Next**.
3. Configure the first mapping for the user's email address:
    - **Name**: `Zulip email`
    - **SAML Attribute Name**: `email`
    - **Expression**:

        ```python
        return request.user.email
        ```

4. Click **Finish** to save the mapping.
5. Repeat the process to create the user's full name mapping:
    - **Name**: `Zulip full name`
    - **SAML Attribute Name**: `full_name`
    - **Expression**:

        ```python
        return request.user.name or request.user.username
        ```

6. Click **Finish** to save the mapping.

### Create an application and provider

<SAMLProvider20265Warning />

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to create an application and provider pair.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **Slug** because it will be required later.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set the **ACS URL** to `https://zulip.company/complete/saml/`.
        - Set the **Audience** to `https://zulip.company`.
        - Set the **SLS URL** to `https://zulip.company/complete/saml/`.
        - Under **Advanced protocol settings**:
            - Select an available **Signing Certificate**.
            - Set **NameID Property Mapping** to `Zulip email`.
            - Add the `Zulip email` and `Zulip full name` property mappings to **Selected User Property Mappings**.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## Zulip configuration

Zulip is a Django application and is configured with `/etc/zulip/settings.py`. Make sure that your `settings.py` file includes the current Zulip SAML authentication section before changing the settings below.

1. Uncomment `zproject.backends.SAMLAuthBackend` in `AUTHENTICATION_BACKENDS`.
2. In the `SAML Authentication` section, configure authentik as a SAML IdP:

    ```python title="/etc/zulip/settings.py"
    SOCIAL_AUTH_SAML_ORG_INFO = {
        "en-US": {
            "displayname": "authentik Zulip",
            "name": "zulip",
            "url": "{}{}".format("https://", EXTERNAL_HOST),
        },
    }

    SOCIAL_AUTH_SAML_ENABLED_IDPS: dict[str, Any] = {
        "authentik": {
            "entity_id": "https://authentik.company/application/saml/<application_slug>/metadata/",
            "url": "https://authentik.company/application/saml/<application_slug>/",
            "attr_user_permanent_id": "email",
            "attr_username": "email",
            "attr_email": "email",
            "attr_full_name": "full_name",
            "display_name": "authentik SAML",
        },
    }
    ```

3. Download the signing certificate from the authentik SAML provider and place it at `/etc/zulip/saml/idps/authentik.crt`.
4. Set the certificate permissions expected by Zulip:

    ```bash
    chown -R zulip.zulip /etc/zulip/saml/
    find /etc/zulip/saml/ -type f -exec chmod 644 -- {} +
    ```

5. Restart Zulip.

## Configuration verification

To confirm that authentik is properly configured with Zulip, open Zulip and click **Log in with authentik SAML**. After you authenticate with authentik, you should be redirected back to Zulip.

## Resources

- [Zulip documentation - SAML authentication for self-hosted servers](https://zulip.readthedocs.io/en/stable/production/authentication-methods.html#saml)
- [Zulip Help Center - SAML authentication](https://zulip.com/help/saml-authentication)
- [Zulip source - production settings template](https://github.com/zulip/zulip/blob/main/zproject/prod_settings_template.py)
