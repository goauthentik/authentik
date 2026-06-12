---
title: Integrate with HubSpot
sidebar_label: HubSpot
support_level: community
---

import SAMLProvider20265Warning from "../../\_saml-provider-2026-5-warning.mdx";

## What is HubSpot?

> HubSpot is a customer platform with tools for CRM, marketing, sales, customer service, content management, operations, and commerce.
>
> -- https://www.hubspot.com/

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.

:::info HubSpot requirements
This guide covers SAML Single Sign-On (SSO) for HubSpot. HubSpot SSO requires a HubSpot Professional or Enterprise account, or an active Professional or Enterprise trial, and a HubSpot user with **Super Admin** permissions. HubSpot identifies SSO users by email address, so the NameID sent by authentik must match the user's email address in HubSpot.
:::

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of HubSpot with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

<SAMLProvider20265Warning />

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: set **Application Name**, **Slug**, an optional group, the policy engine mode, and optional UI settings. Take note of the **Slug** as it will be required later.
    - **Choose a Provider**: select **SAML Provider** on the **Choose a Provider Type** page.
    - **Configure SAML Provider**: provide a name (or accept the auto-provided name), select the authorization flow to use for this provider, and set the following values.
        - Set **ACS URL** to `https://temp.temp`.
        - Set **Audience** to `https://temp.temp`.
        - Under **Advanced protocol settings**:
            - Select an available **Signing Certificate**.
            - Set **NameID Property Mapping** to `authentik default SAML Mapping: Email`.
            - Set **Service Provider Binding** to **Post**.
            - Set **Default NameID Policy** to **Email address**.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Create Application** to save the new application and provider.

### Copy the SAML values from authentik

1. In the authentik Admin interface, navigate to **Applications** > **Providers** and click the SAML provider that you created for HubSpot.
2. Copy the **SAML Endpoint** value. This value is required in HubSpot.
3. Under **Related objects** > **Download signing certificate**, click **Download**.
4. Open the downloaded certificate file and copy the full PEM certificate.

## HubSpot configuration

1. Log in to HubSpot as a Super Admin.
2. In the top navigation bar, click the **settings** icon.
3. In the left sidebar, navigate to **Security**.
4. On the **Login** tab, do one of the following:
    - If portal login settings have not been configured yet, click **Setup Portal Login Settings**.
    - If portal login settings have already been configured, click **Set up** in the **Configure single sign-on (SSO)** section.
5. In the right panel, select the **All Other Identity Providers** tab.
6. Set the following values:
    - **Identity Provider Identifier or Issuer URL**: `https://authentik.company/application/saml/<application_slug>/metadata/`
    - **Identity Provider Single Sign-On URL**: the **SAML Endpoint** value from authentik.
    - **X.509 Certificate**: the full PEM certificate that you downloaded from authentik.
7. Copy the following values from HubSpot. You will use them to finish the SAML provider configuration in authentik.
    - **Audience URI**
    - **ACS URL**
8. Keep the SSO setup panel open.

## Configure the remaining information in authentik

1. In the authentik Admin interface, navigate to **Applications** > **Providers** and click the SAML provider that you created for HubSpot.
2. Click **Edit**.
3. Under **Protocol settings**, set the following values:
    - **ACS URL**: the **ACS URL** value from HubSpot.
    - **Audience**: the **Audience URI** value from HubSpot.
4. Click **Save Changes**.

## Verify HubSpot configuration

1. Return to the HubSpot SSO setup panel.
2. Click **Verify** and complete the authentik login flow.

## Configuration verification

To confirm that authentik is properly configured with HubSpot, open HubSpot in a private browser window, click **Log in with SSO**, and enter the email address of a HubSpot user whose email address matches an authentik user.

## Resources

- [HubSpot Knowledge Base - Set up single sign-on (SSO)](https://knowledge.hubspot.com/account-security/set-up-single-sign-on-sso)
- [HubSpot - Single Sign-on in HubSpot](https://www.hubspot.com/products/single-sign-on)
- [Cisco Duo - Duo Single Sign-On for HubSpot](https://duo.com/docs/sso-hubspot)
