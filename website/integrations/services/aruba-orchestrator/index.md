---
title: Integrate with Aruba Orchestrator
sidebar_label: Aruba Orchestrator
---

# Integrate with Aruba Orchestrator

<span class="badge badge--secondary">Support level: Community</span>

## What is Aruba Orchestrator

> Aruba Orchestrator is a network management platform used to centrally manage, configure, monitor, and automate Aruba network devices and services. It provides tools for network visibility, policy management, and performance monitoring, simplifying the administration of complex and distributed network environments.
>
> -- https://www.hpe.com/us/en/aruba-edgeconnect-sd-wan.html

## Preparation

The following placeholders are used in this guide:

- `arubaorchestrator.company` is the FQDN of the Aruba Orchestrator installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik Configuration

1. From the **authentik Admin interface** and go to **Customization** -> **Property Mappings**, then click **Create**.
2. Choose **SAML Provider Property Mapping**, and click **Next**.
3. Configure the following:
    - Set **Name** to `Aruba Orchestrator RBAC`.
    - Set **SAML Attribute Name** to `sp-roles`.
    - Add the expression below, modifying the group name if necessary:
        ```python
        if ak_is_group_member(request.user, name="authentik Admins"):
            result = "superAdmin"
        return result
        ```
4. When satisfied with the expression, click **Create**.
5. Navigate to **Applications** -> **Applications** in the **authentik Admin interface**, and create a new application with a **SAML** provider using the wizard. During the setup:
    - Set the **ACS URL** and **Issuer** to `https://arubaorchestrator.company/gms/rest/authentication/saml2/consume`.
    - Choose `Post` for the **Service Provider Binding**.
    - Under **Advanced protocol settings**, select an available signing certificate.
    - Add the `sp-roles` property mapping under the **Proprety Mappins** section of **Advanced protocol settings**.
6. Go to **Applications** -> **Providers** -> **Provider for _Your application name_**, and download the signing certificate.

## Aruba Orchestrator Configuration

1. Log in to the Aruba Orchestrator.
2. Create a new Remote Authentication Server under **Orchestrator** -> **Authentication** -> **Add New Server**.
    - **Type**: `SAML`
    - **Name**: `authentik`
    - **Username Attribute**: `http://schemas.goauthentik.io/2021/02/saml/username`
    - **Issuer URL**: `https://arubaorchestrator.company/gms/rest/authentication/saml2/consume`
    - **SSO Endpoint**: `https://authentik.company/application/saml/<slug>/sso/binding/init/` (replace \<slug\> with application slug name)
    - **IdP X509 Cert**: (paste in the downloaded signing certificate)
    - **ACS URL**: `https://arubaorchestrator.company/gms/rest/authentication/saml2/consume`
    - **EdgeConnect SLO Endpoint**: `https://arubaorchestrator.company/gms/rest/authentication/saml2/logout`
    - **iDP SLO Endpoint**: (optional)
    - **EdgeConnect X.509 Cert SLO**: (optional)
    - **Roles Attribute**: `sp-roles` (optional)
    - **Appliance Access Group Attribute**: (optional)
    - **Default role**: (optional)

## Verification

1. Go to `https://arubaorchestrator.company`.
2. Click **Log In Using authentik** on the login screen and authorize with authentik.
3. You will be redirected to the home screen of the Aruba Orchestrator.
