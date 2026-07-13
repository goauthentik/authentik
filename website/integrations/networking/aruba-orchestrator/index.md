---
title: Integrate with Aruba Orchestrator
sidebar_label: Aruba Orchestrator
support_level: community
---

## What is Aruba Orchestrator?

> Aruba Orchestrator, part of HPE Aruba Networking EdgeConnect SD-WAN, provides centralized management, monitoring, and orchestration for EdgeConnect appliances and SD-WAN fabrics.
>
> -- https://www.hpe.com/us/en/aruba-edgeconnect-sd-wan.html

## Preparation

The following placeholders are used in this guide:

- `arubaorchestrator.company` is the FQDN of the Aruba Orchestrator installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Aruba Orchestrator with authentik, you need to create a SAML property mapping, an application/provider pair, and application entitlements for the Orchestrator RBAC roles users should receive.

Aruba Orchestrator requires either a role attribute or a default role for SAML users. This guide sends assigned authentik application entitlement names in the `sp-roles` SAML attribute.

### Create property mappings

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**. Create a **SAML Provider Property Mapping** with the following settings:
    - **Name**: provide a descriptive name, such as `Aruba Orchestrator roles`.
    - **SAML Attribute Name**: `sp-roles`
    - **Expression**:
        ```python
        roles = [
            entitlement.name
            for entitlement in request.user.app_entitlements(provider.application)
        ]
        return roles if roles else None
        ```

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **Slug** value because it will be required later.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set the **ACS URL** to `https://arubaorchestrator.company/gms/rest/authentication/saml2/consume`.
        - Set the **Audience** to `https://arubaorchestrator.company/gms/rest/authentication/saml2/consume`.
        - Under **Advanced protocol settings**, select an available **Signing certificate**.
        - Under **Advanced protocol settings** > **Property mappings**, add the newly created property mapping.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

4. Navigate to **Applications** > **Providers**, open the provider you created, and download the signing certificate.

### Create application entitlements

Use [application entitlements](/docs/add-secure-apps/applications/manage_apps/#application-entitlements) to represent the Orchestrator RBAC roles that this application should assign.

1. Open the Aruba Orchestrator application that you just created in the authentik Admin interface.
2. Click the **Application entitlements** tab.
3. Create one entitlement for each Orchestrator RBAC role that users should be able to receive, such as `SuperAdmin`, `Monitor`, or a custom Orchestrator role name.
4. Bind the appropriate users or groups to each entitlement.

Each entitlement name must exactly match the Orchestrator RBAC role value. These values are case-sensitive.

## Aruba Orchestrator configuration

1. Log in to the Aruba Orchestrator.
2. Navigate to **Orchestrator** > **Orchestrator Server** > **Users & Authentication** > **Authentication** and click **+Add New Server**.
3. Select `SAML` as the server type and configure the following values:
    - **Name**: `authentik`
    - **Username Attribute**: `http://schemas.goauthentik.io/2021/02/saml/username`
    - **Issuer URL**: `https://authentik.company/application/saml/<application_slug>/metadata/`
    - **SSO Endpoint**: `https://authentik.company/application/saml/<application_slug>/init/`
    - **IdP X.509 Cert**: paste the downloaded signing certificate.
    - **Roles Attribute**: `sp-roles`
4. If you do not assign application entitlements for every user who can access Orchestrator, set **Default role** to the fallback RBAC role users should receive.
5. Click **Save**.

The **ACS URL** and **EdgeConnect SLO Endpoint** fields are generated by Aruba Orchestrator. For self-hosted Orchestrator deployments, ensure these URLs use the public Orchestrator FQDN or public IP address that authentik can reach.

## Configuration verification

To confirm that authentik is properly configured with Aruba Orchestrator, open Aruba Orchestrator and click **Log In Using authentik** on the login screen.

## Resources

- [HPE Aruba Networking EdgeConnect SD-WAN Orchestrator authentication documentation](https://arubanetworking.hpe.com/techdocs/sdwan/docs/orch/orchestrator/server/remote-auth/)
- [HPE Aruba Networking EdgeConnect SD-WAN Orchestrator RBAC documentation](https://arubanetworking.hpe.com/techdocs/sdwan/docs/orch/orchestrator/server/rbac/)
