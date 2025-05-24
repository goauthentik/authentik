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

## authentik Configuration

To support the integration of OVHcloud with authentik, you need to create an application/provider pair in authentik.

### Create an Application and Provider in authentik

1. Log in to authentik as an admin and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively, you can first create a provider separately, then create the application and connect it with the provider.)

    - **Application**: Provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: Select **SAML Provider** as the provider type.
    - **Configure the Provider**: Provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations:
        - Set the **ACS URL** to `https://www.ovhcloud.com/eu/auth/saml/acs` for EU region, or `https://www.ovhcloud.com/ca/auth/saml/acs` for CA region.
        - Set the **Service Provider Binding** to `Post`.
        - Under **Advanced protocol settings**, set an available signing certificate.

    - **Configure Bindings** _(optional)_: You can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

### Download metadata file

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click on the name of the provider that you created in the previous section.
3. Under **Related objects** > **Metadata**, click on **Download**. This downloaded file is your **SAML Metadata** file and it will be required in the next section.

## OVHcloud Configuration

1. Log in to the **OVHcloud Control Panel**.
2. Click your name in the top right corner. In the sidebar that appears, click your name again.
3. Select **Identity and Access Management (IAM)** from the left-hand menu.
4. Click the **Identities** tab to access local users management and switch to the **SSO** tab.
5. Click on the **SSO Connection** button.
    - If you want to keep local OVH users, tick the **Keep active OVHcloud users** box.
    - Open the File you downloaded in [Download metadata file](#download-metadata-file). Copy the content and paste it into the **XML-Metadata** field.
6. Close the window by clicking **Confirm**.

## Configuration Verification

To verify that authentik is correctly integrated with OVH Cloud, first log out of your account. On the OVHcloud login page, enter your [OVH Customer ID/NIC handle](https://help.ovhcloud.com/csm/en-account-create-ovhcloud-account?id=kb_article_view&sysparm_article=KB0043022#what-is-my-nic-handle) followed by `/idp` (e.g. `xx1111-ovh/idp`) without entering a password, and click the Login button.

You will be redirected to your authentik installation for authentication. Once authenticated you will be logged in to OVHcloud.

