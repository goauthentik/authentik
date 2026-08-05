---
title: Integrate with OVHcloud
sidebar_label: OVHcloud
support_level: community
---

import SAMLProvider20265Warning from "../../\_saml-provider-2026-5-warning.mdx";

## What is OVHcloud?

> OVHcloud is a cloud provider that offers public and private cloud services, web hosting, dedicated servers, and domain services.
>
> -- https://www.ovhcloud.com

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of OVHcloud with authentik, you need to create a SAML property mapping, an application/provider pair, and application entitlements for the OVHcloud user groups that users should receive.

### Create a group property mapping

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**.
3. Select **SAML Provider Property Mapping** as the type and click **Next**.
4. Configure the property mapping:
    - **Name**: provide a descriptive name, such as `OVHcloud groups`.
    - **SAML Attribute Name**: set the value for your OVHcloud region:
        - EU and CA: `Group`
        - US: `groups`
    - **Expression**:
        ```python
        return [
            entitlement.name
            for entitlement in request.user.app_entitlements(provider.application)
        ]
        ```
5. Click **Finish**.

### Create an application and provider

<SAMLProvider20265Warning />

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations:
        - Set **ACS URL** to the value for your OVHcloud region:
            - EU: `https://www.ovhcloud.com/eu/auth/saml/acs`
            - CA: `https://www.ovhcloud.com/ca/auth/saml/acs`
            - US: `https://us.ovhcloud.com/auth/`
        - Set **Audience** to the value for your OVHcloud region:
            - EU: `https://www.ovhcloud.com/eu/auth/`
            - CA: `https://www.ovhcloud.com/ca/auth/`
            - US: `https://us.ovhcloud.com/auth/`
        - Under **Advanced protocol settings**:
            - Set an available **Signing Keypair**.
            - Under **Property mappings**, add the OVHcloud groups mapping and remove `authentik default SAML Mapping: Groups`.

    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

### Download metadata file

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click on the name of the provider that you created in the previous section.
3. Under **Related objects** > **Metadata**, click **Download**. This downloaded file is your SAML metadata file and is required in the next section.

### Create application entitlements

Use [application entitlements](/docs/add-secure-apps/applications/manage_apps/#application-entitlements) to represent the OVHcloud user groups that this application should send.

1. In the Admin interface, navigate to **Applications** > **Applications** and open the OVHcloud application.
2. Click the **Application entitlements** tab.
3. Click **Create**, enter the name of an OVHcloud user group that authentik should send, and click **Create** again.
4. Bind the appropriate users or groups to the entitlement.
5. Repeat these steps for each OVHcloud user group that authentik should send.

## OVHcloud configuration

To integrate authentik with OVHcloud, configure authentik as the trusted identity provider for your OVHcloud account. You also need to declare OVHcloud user groups that match the group names that authentik sends in the SAML assertion.

### Configure the SSO connection

1. Log in to the OVHcloud Control Panel.
2. Click your name in the top-right corner, and in the sidebar that appears, click your name again.
3. Select **Identity and Access Management (IAM)** from the left-hand menu.
4. Click the **Identities** tab to access local users management and switch to the **SSO** tab.
5. Click **SSO Connection** and configure the following settings:
    - **XML-Metadata**: open the file that you downloaded in [Download metadata file](#download-metadata-file), copy the content, and paste it into this field.
    - **User Attribute Name**: for EU and CA accounts, set this to `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/upn`.
    - **Group Attribute Name**: set this to the **SAML Attribute Name** value from the OVHcloud groups property mapping.
    - **Keep active OVHcloud users** _(optional)_: enable this option if you want to keep local OVHcloud users active.
6. Click **Confirm**.

### Declare user groups

OVHcloud authorizes federated users through OVHcloud user groups. The group name in OVHcloud must match an OVHcloud application entitlement name in authentik.

1. In the **Identities** section, open the **User groups** tab.
2. Click **Declare a group**.
3. Configure the following settings:
    - **Group name**: enter an OVHcloud application entitlement name from authentik.
    - **Role**: select the OVHcloud role for this group.
4. Click **Confirm**.
5. Repeat these steps for each OVHcloud application entitlement that should grant access to OVHcloud.

If you select the `NONE` role, assign permissions to the group with OVHcloud IAM policies.

## Configuration verification

To confirm that authentik is properly configured with OVHcloud, log out of your OVHcloud account. On the OVHcloud login page, enter your [OVH Customer ID/NIC handle](https://help.ovhcloud.com/csm/en-account-create-ovhcloud-account?id=kb_article_view&sysparm_article=KB0043022#what-is-my-nic-handle) followed by `/idp`, leave the password field blank, and click **Login**.

After you are redirected to authentik and successfully authenticate, OVHcloud signs you in.

## Resources

- [OVHcloud documentation - Enabling Okta SSO connections with your OVHcloud account](https://docs.ovhcloud.com/en/guides/account-and-service-management/account-information/ovhcloud-account-connect-saml-okta)
- [OVHcloud US support - Enabling Okta SSO connections with your OVHcloud account](https://support.us.ovhcloud.com/hc/en-us/articles/16487697807635-Enabling-Okta-SSO-connections-with-your-OVHcloud-account)
