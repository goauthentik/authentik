---
title: Integrate with Knocknoc
sidebar_label: Knocknoc
support_level: community
---

## What is Knocknoc?

> Knocknoc links your single sign-on experience to existing network access controls. It can dynamically orchestrate network access controls (e.g., managing firewall rules in real-time without exposing target machines) or function as an identity-aware gateway.
>
> -- https://knocknoc.io/

## Preparation

The following placeholders are used in this guide:

- `knocknoc.company` is the FQDN of the Knocknoc installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Knocknoc with authentik, create SAML property mappings and an application/provider pair in authentik.

### Create property mappings

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**. Create the following **SAML Provider Property Mapping** entries:
    - **Real name mapping**:
        - **Name**: `SAML to Knocknoc realName`
        - **SAML Attribute Name**: `realName`
        - **Expression**:

            ```python
            return user.name
            ```

    - **Groups mapping**:
        - **Name**: `SAML to Knocknoc groups`
        - **SAML Attribute Name**: `groups`
        - **Expression**:

            ```python
            for group in user.groups.all():
                yield group.name
            ```

    - **Session duration mapping**:
        - **Name**: `SAML to Knocknoc session duration`
        - **SAML Attribute Name**: `sessionDuration`
        - **Expression**:

            ```python
            return 540
            ```

:::info Group names
Knocknoc users are created automatically after SAML login, but their group membership must match an existing Knocknoc group or Knoc before they receive access. Ensure the group names sent by authentik match the group names configured in Knocknoc.
:::

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Under **Protocol settings**:
            - **ACS URL**: `https://knocknoc.company/api/saml/acs`
            - **Audience**: `https://knocknoc.company/api/saml/metadata`
        - Under **Advanced protocol settings**:
            - Select any available **Signing Certificate**.
            - Add the three property mappings you created in the previous section to **Selected User Property Mappings**.
            - Set **NameID Property Mapping** to `authentik default SAML Mapping: Username`.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

### Copy the metadata URL

1. Navigate to **Applications** > **Providers** and click on the name of the Knocknoc provider (e.g. `Provider for Knocknoc`).
2. Under **Related objects** > **Metadata**, click **Copy download URL**. This metadata URL is required in the Knocknoc configuration.

## Knocknoc configuration

1. Log in to the Knocknoc admin interface and navigate to **Settings**.
2. Configure the following settings:
    - **Public URL**: `https://knocknoc.company`
    - **Metadata URL**: paste the metadata URL copied from authentik.
3. Click **Generate new keypair**.
4. Click **Save**.

:::info Manual keypair generation
If you want to generate the Knocknoc keypair manually instead, run the following command on a Linux host and upload the generated certificate and key files in Knocknoc.

```shell
openssl req -new -x509 -days 3650 -nodes -subj /CN=Knocknoc/ -out <certificate_filename>.crt -keyout <certificate_key_filename>.key
```

:::

## Configuration verification

To confirm that authentik is properly configured with Knocknoc, log out and open Knocknoc. Click **SSO Login** and authenticate with authentik.

## Resources

- [Knocknoc Docs - SAML](https://docs.knocknoc.io/books/admin-guide/page/saml)
- [Knocknoc Docs - SAML with Authentik](https://docs.knocknoc.io/books/admin-guide/page/saml-with-authentik)
- [Knocknoc Docs - Settings](https://docs.knocknoc.io/books/admin-guide/page/settings)
