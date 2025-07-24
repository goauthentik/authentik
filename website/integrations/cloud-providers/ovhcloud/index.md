---
title: Integrate with OVHcloud
sidebar_label: OVHcloud
support_level: community
---

## What is OVHcloud

> OVHcloud is a French cloud provider. They provide public and private cloud products, shared hosting, and dedicated servers in 140 countries.
>
> -- https://www.ovhcloud.com

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.

## authentik configuration

To support the integration of OVHcloud with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively, you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: Provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: Select **SAML Provider** as the provider type.
    - **Configure the Provider**: Provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations:
        - Set the **ACS URL** to:
            - `https://www.ovhcloud.com/eu/auth/saml/acs` for EU region.
            - `https://www.ovhcloud.com/ca/auth/saml/acs` for CA region.
            - `https://us.ovhcloud.com/auth/` for US region.
        - Set the **Service Provider Binding** to `Post`.
        - Under **Advanced protocol settings**, set an available signing certificate.

    - **Configure Bindings** _(optional)_: You can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

### Download metadata file

1. Log in to authentik as an administrator, and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click on the name of the provider that you created in the previous section.
3. Under **Related objects** > **Metadata**, click on **Download**. This downloaded file is your **SAML Metadata** file and it will be required in the next section.

## OVHcloud Configuration

1. Log in to the OVHcloud Control Panel.
2. Click your name in the top right corner, and in the sidebar that appears, click your name again.
3. Select **Identity and Access Management (IAM)** from the left-hand menu.
4. Click the **Identities** tab to access local users management and switch to the **SSO** tab.
5. Click on the **SSO Connection** button.
    - If you want to keep local OVH users, tick the **Keep active OVHcloud users** box.
    - Open the File you downloaded in [Download metadata file](#download-metadata-file). Copy the content and paste it into the **XML-Metadata** field.
6. Close the window by clicking **Confirm**.

## Configuration verification

To verify that authentik is properly integrated with OVHcloud, first log out of your account. On the OVHcloud login page, enter your [OVH Customer ID/NIC handle](https://help.ovhcloud.com/csm/en-account-create-ovhcloud-account?id=kb_article_view&sysparm_article=KB0043022#what-is-my-nic-handle) followed by `/idp` (e.g., `xx1111-ovh/idp`), leave the password field blank, and click **Login**.

You’ll be redirected to your authentik instance to complete authentication. Once successful, you’ll be logged in to OVHcloud.

## References

- [OVHcloud Help Center - User management & Federation](https://help.ovhcloud.com/csm/en-ie-documentation-manage-operate-user-federation?id=kb_browse_cat&kb_id=3d4a8129a884a950f07829d7d5c75243&kb_category=21734cbe50d47d90476b12dfd60b3542&spa=1)
- [OVHcloud US Help Center - User management & Federation](https://support.us.ovhcloud.com/hc/en-us/sections/27230986868883-Federation)
