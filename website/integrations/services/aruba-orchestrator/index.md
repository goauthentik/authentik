---
title: Integrate with Aruba Orchestrator
sidebar_label: Aruba Orchestrator
---

# Aruba Orchestrator

<span class="badge badge--secondary">Support level: Community</span>

## What is Aruba Orchestrator

> Aruba Orchestrator is a network management platform used to centrally manage, configure, monitor, and automate Aruba network devices and services. It provides tools for network visibility, policy management, and performance monitoring, simplifying the administration of complex and distributed network environments.
>
> -- https://www.hpe.com/us/en/aruba-edgeconnect-sd-wan.html

## Preparation

The following placeholders are used in this guide:

- `arubaorchestrator.company` is the FQDN of the Aruba Orchestrator installation.
- `authentik.company` is the FQDN of the authentik installation.
- `SSL Certificate` is the name of the SSL certificate used to sign outgoing responses.

:::note
This documentation lists only the settings that have been changed from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik Configuration

1. Log in to authentik as an admin, and go to the Admin interface.
2. Create a new SAML Property Mapping under **Customisation** -> **Property Mappings**:

    - **Name**: `Aruba Orchestrator RBAC`
    - **SAML Attribute Name**: `sp-roles`
    - **Expression**: Use the expression below but amend the group name as desired.

    ```
    if ak_is_group_member(request.user, name="authentik Admins"):
              result = "superAdmin"
         return result
    ```

    - Save the settings.

3. Create a new SAML Provider under **Applications** -> **Providers** using the following settings:
    - **Name**: Aruba Orchestrator
    - **Authentication Flow**: Use your preferred authentication flow (e.g., default-authentication-flow`)
    - **Authorization Flow ID**: `default-provider-authorization-explicit-consent (Authorize Application)`
    - Protocol settings:
    -   - **ACS URL**: `https://arubaorchestrator.company/gms/rest/authentication/saml2/consume`
    -   - **Issuer**: `https://arubaorchestrator.company/gms/rest/authentication/saml2/consume`
    -   - **Service Provider Binding**: Post
    - Advanced protocol settings:
    -   - **Signing Certificate**:`SSL Certificate`
    -   - **Property Mappings**:`default` + `sp-roles`
    - Leave everything else as default and save the settings.
4. Download the signing certificate under **Applications** -> **Providers** -> **Aruba Orchestrator** .
5. Create a new application under **Applications** -> **Applications**, pick a name and a slug, and assign the provider that you have just created.

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
