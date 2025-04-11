---
title: Integrate with Knocknoc
sidebar_label: Knocknoc
support_level: community
---

## What is Knocknoc

> Knocknoc links your single-sign on experience to existing network access controls. It can dynamically orchestrate network access controls (e.g., managing firewall rules in real-time without exposing target machines) or function as an identity-aware gateway.
>
> -- https://knocknoc.io/

## Preparation

The following placeholders are used in this guide:

- `knocknoc.company` is the FQDN of the Knocknoc installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Knocknoc with authentik, you need to create an application/provider pair and 3 property mappings in authentik.

### Create property mappings in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create** to create a property mapping.

- **Select type**: Select **SAML Provider Property Mapping** as the type and click **Next**.
- **Create SAML Provider Property Mapping**:

    - **Name**: provide a descriptive name (e.g. `SAML to Knocknoc realName`)
    - **SAML Attribute Name**: `realName`
    - **Expression**:

    ```python
    return user.name
    ```

3. Click **Finish** to save the new property mapping.
4. Repeat steps 1-3 two more times, with the following configurations:

- **Select type**: Select **SAML Provider Property Mapping** as the type and click **Next**.
- **Create SAML Provider Property Mapping**:

    - **Name**: provide a descriptive name (e.g. `SAML to Knocknoc groups`)
    - **SAML Attribute Name**: `groups`
    - **Expression**:

    ```python
    for group in user.ak_groups.all(): yield group.name
    ```

- **Select type**: Select **SAML Provider Property Mapping** as the type and click **Next**.
- **Create SAML Provider Property Mapping**:

    - **Name**: provide a descriptive name (e.g. `SAML to Knocknoc session duration`)
    - **SAML Attribute Name**: `sessionDuration`
    - **Expression**:

    ```python
    return 540
    ```

:::note
This example will set session duration at 540 minutes. Change the value to match your desired session duration length in minutes.
:::

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **SAML Provider** as the provider type.
- **Configure Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
  **Protocol Settings**:
    - **ACS URL**: <kbd>https://<em>knocknoc.company</em>/api/saml/acs</kbd>
    - **Issuer**: <kbd>https://<em>authentik.company</em></kbd>
    - **Service Provider Binding**: `Post`
    - **Audience**: <kbd>https://<em>kocknoc.company</em>/api/saml/metadata</kbd>
    - Under **Advanced protocol settings**, add the three **Property Mappings** you created in the previous section, then set the **NameID Property Mapping** to `Authentik default SAML Mapping: Username`.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

### Get the metadata URL of the Knocknoc provider

1. Navigate to **Applications** > **Providers** and click on the name of the Knocknoc provider (e.g. `Provider for Knocknoc`).
2. Navigate to the **Related objects** section and click on **Copy download URL**. This is the `SAML Metadata URL` and will be needed in the next section.

## Knocknoc configuration

1. Log in to Knocknoc and navigate to **Admin** > **Settings** > **SAML**
2. Set the following configuration:

    - **Metadata URL**: **SAML Metadata URL** copied from the authentik provider.
    - **Public URL**: <kbd>https://<em>knocknoc.company</em></kbd>
    - **Key file**: select a key file.
    - **Cert file**: select a certificate file.

3. Click on **Save**.

:::note
Key file and Cert file are currently required fields in Knocknoc. You can generate a certificate and key on a Linux host with this command:
`openssl req -new -x509 -days 3650 -nodes -subj /CN=Knocknoc/ -out <certificate_filename>.crt -keyout <certificate_key_filename>.key`
:::

## Configuration verification

To confirm that authentik is properly configured with Knocknoc, log out and log back in using authentik credentials.
