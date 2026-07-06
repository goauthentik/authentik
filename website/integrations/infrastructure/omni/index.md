---
title: Integrate with Omni
sidebar_label: Omni
support_level: community
---

import SAMLProvider20265Warning from "../../\_saml-provider-2026-5-warning.mdx";

## What is Omni?

> Talos Omni ships with all the parts you otherwise need to glue together: fleet upgrade orchestration, encryption across sites, identity management, cluster templates.
>
> -- https://www.siderolabs.com/omni-for-kubernetes-cluster-management

## Preparation

The following placeholders are used in this guide:

- `omni.company` is the FQDN of the Omni installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Omni with authentik, you need to create a property mapping and application/provider pair in authentik.

### Create an email property mapping

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**.
3. Select **SAML Provider Property Mapping** as the property mapping type.
4. Set the following values:
    - **Name**: `Omni email`
    - **SAML Attribute Name**: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name`
    - **Expression**:

        ```python
        return request.user.email
        ```

5. Click **Finish**.

### Create an application and provider

<SAMLProvider20265Warning />

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **Slug** value because it will be required later.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set the **ACS URL** to `https://omni.company/saml/acs`.
        - Set the **Audience** to `https://omni.company/saml/metadata`.
        - Under **Advanced protocol settings**:
            - Select an available **Signing certificate**.
            - Enable **Sign assertions** and **Sign responses**.
            - Add the `Omni email` property mapping that you created in the previous section to **Property mappings**.
            - Set **NameID Property Mapping** to `Omni email`.
            - Set **Default NameID Policy** to **Email address**.
    - **Configure Bindings** _(optional)_: create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to control which users can access the Omni application from the **Application Dashboard** page.

3. Click **Submit**.

## Omni configuration

For self-hosted Omni, enable SAML and set the authentik metadata URL in your Omni configuration.

```shell
--auth-saml-enabled=true
--auth-saml-url=https://authentik.company/application/saml/<application_slug>/metadata/
```

If you use the Sidero Labs Docker Compose deployment, add the flags to the `AUTH` value in your environment file.

```env title=".env"
AUTH='--auth-saml-enabled=true \
      --auth-saml-url=https://authentik.company/application/saml/<application_slug>/metadata/'
```

Restart Omni for the changes to take effect.

For Sidero Labs SaaS Omni, SAML must be enabled by Sidero Labs support or your account manager. Provide them with the authentik metadata URL from this section.

## Configuration verification

To confirm that authentik is properly configured with Omni, open Omni, log out, and log back in with SAML.

## Resources

- [Sidero Labs Documentation - Using SAML with Omni](https://docs.siderolabs.com/omni/security-and-authentication/using-saml-with-omni/overview)
- [Sidero Labs Documentation - Configure Entra ID for Omni](https://docs.siderolabs.com/omni/security-and-authentication/using-saml-with-omni/how-to-configure-entraid-for-omni)
- [Sidero Labs Documentation - Authentication and Authorization](https://docs.siderolabs.com/omni/security-and-authentication/authentication-and-authorization)
- [Sidero Labs Documentation - Omni Configuration](https://docs.siderolabs.com/omni/reference/omni-configuration)
