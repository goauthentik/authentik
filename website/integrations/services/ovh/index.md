---
title: Integrate with OVH Cloud
sidebar_label: OVH Cloud
support_level: community
---

## What is OVH Cloud

> OVH Cloud is a French cloud provider. They provide public and private cloud products, shared hosting, and dedicated servers in 140 countries.
>
> -- https://www.ovhcloud.com

## Preparation

The following placeholders are used in this guide:

- `0123-456-78` is your OVH Customer Code.
- `authentik.company` is the FQDN of the authentik installation.

## authentik Configuration

To support the integration of OVH Cloud with authentik, you need to create an application/provider pair in authentik.

### Create an Application and Provider in authentik

1. Log in to authentik as an admin and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively, you can first create a provider separately, then create the application and connect it with the provider.)

    - **Application**: Provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: Select **SAML Provider** as the provider type.
    - **Configure the Provider**: Provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations:
        - Set the **ACS URL** to `https://www.ovhcloud.com/eu/auth/saml/acs`.
        - Set the **Service Provider Binding** to `Post`.
        - In **Advanced protocol settings**, select a **Signing Certificate** and check that **Sign assertions** is enabled.

    - **Configure Bindings** _(optional)_: You can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Service Configuration

1. Go to [OVH Cloud](https://www.ovhcloud.com) and log in.
2. Click on your **name** in the top right corner. Then, click on your **name** again in the sidebar that opens.
3. Select **Identity and Access Management (IAM)** from the left-hand menu.
4. Click the **Identities** tab to access local users management and switch to the **SSO** tab.
5. Click on the **SSO Connection** button.
    - If you want to keep local OVH users, tick the `Keep active OVHcloud users` box.
    - Copy the XML-Metadata from your authentik installation (Applications -> Providers -> Your OVH Provider -> Metadata) to the **XML-Metadata** field.
6. Close the window by clicking **Confirm**.

## Configuration Verification

Log out of your OVH Account. To log in with authentik, enter your OVH Customer Code followed by `/idp` in the **username** field (0123-456-78/idp). You will be redirected to your authentik installation and can log in.
