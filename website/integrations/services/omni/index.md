---
title: Integrate with Omni
sidebar_label: Omni
support_level: community
---

## What is Omni

> Omni manages Kubernetes on bare metal, virtual machines, or in a cloud.
>
> -- https://github.com/siderolabs/omni

## Preparation

The following placeholders are used in this guide:

- `omni.company` is the FQDN of the Omni installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Omni with authentik, you need to create a property mapping and application/provider pair in authentik.

### Create a Property Mapping, Application and Provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create** to create a property mapping.

- **Choose a Property Mapping type**: Select SAML Provider Property Mapping as the property mapping type.

- **Configure the Property Mapping**:
    - **Name**: `*property_mapping_name*` (e.g. `Omni Mapping`)
    - **SAML Attribute Name**: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name`
    - **Expression**: `return request.user.email`

3. Navigate to **Applications** -> **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, application slug, an optional group for the type of application, the policy engine mode, and optional UI settings.

- **Choose a Provider type**: select SAML Provider as the provider type.

- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.

    - ACS URL: `<kbd>https://<em>omni.company</em>/saml/acs</kbd>`
    - Service Provider Binding: `Post`
    - Audience: `<kbd>https://<em>omni.company</em>/saml/metadata</kbd>`
    - Signing Certificate: select a signing certificate, either the `authentik Self-signed Certificate` or generate a certificate via **System** > **Certificate**
    - Sign assertions: `true`
    - Sign responses: `true`
    - Property mappings: `<property_mapping_name>` (e.g. `Omni Mapping`)
    - NameID Property Mapping: `<property_mapping_name>` (e.g. `Omni Mapping`)

- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

4. Click **Submit** to save the new application and provider.

## Omni configuration

Add the following environment variables to your Omni configuration. Make sure to fill in the authentik FQDN from your authentik instance and the application slug generated in the last section.

```shell
auth-saml-enabled=true
auth-saml-url=https://<em>authentik.company</em>/application/saml/<em><application_slug></em>/metadata/
```

## Configuration verification

To confirm that authentik is properly configured with Omni, log out and log back in via the SAML button.
