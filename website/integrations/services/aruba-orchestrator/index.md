---
title: Integrate with Aruba Orchestrator
sidebar_label: Aruba Orchestrator
support_level: community
---

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
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Aruba Orchestrator with authentik, you need to create an application/provider pair in authentik.

### Create property mappings

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**. Create a **SAML Provider Property Mapping** with the following settings:
    - **Name**: Set an appropriate name
    - **SAML Attribute Name**: <kbd>sp-roles</kbd>
    - **Friendly Name**: Leave blank
    - **Expression**: (You can modify the <kbd>authentik Admins</kbd> group as needed)
        ```python
        if ak_is_group_member(request.user, name="authentik Admins"):
            result = "superAdmin"
        return result
        ```

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **slug** as it will be required later.
- **Choose a Provider type**: select **SAML Provider** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Set the **ACS URL** and **Issuer** to <kbd>https://<em>arubaorchestrator.company</em>/gms/rest/authentication/saml2/consume</kbd>.
    - Set the **Service Provider Binding** to `Post`.
    - Under **Advanced protocol settings**, select an available signing certificate.
    - Under **Advanced protocol settings**, add the newly created property mapping under **Property Mappings**.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

4. Navigate to **Applications** > **Providers** > **Provider for _Application Name_**, and download the signing certificate.

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
