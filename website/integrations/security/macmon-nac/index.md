---
title: Integrate with macmon NAC
sidebar_label: macmon NAC
support_level: community
---

## What is macmon NAC

> macmon NAC is a network access control platform that provides visibility, policy enforcement, and automated responses for devices connecting to your network.
>
> -- [macmon Network Access Control (NAC)](https://www.belden.com/products/industrial-networking-cybersecurity/software-solutions/macmon-network-access-control-software#sort=%40catalogitemwebdisplaypriority%20ascending&numberOfResults=25)

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.
- `macmon.company` is the FQDN of your macmon NAC environment.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of macmon NAC with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **slug** value because it will be required later.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set the **ACS URL** to `https://macmon.company/login/?acs`.
        - Set the **Issuer** to `https://macmon.company`.
        - Set the **Service Provider Binding** to `Post`.
        - Under **Advanced protocol settings**:
            - Set an available signing certificate.
            - Enable both **Sign Assertions** and **Sign Responses**.
            - Set **NameID Property Mapping** to the email mapping you selected (for example, `authentik default SAML Mapping: Email`).
              macmon NAC expects the NameID format `E-mail address`, so ensure that the chosen mapping provides the user’s email address.
              You can optionally add mappings for additional claims such as `firstName`, `surName`, `memberOf`, or `description` if macmon NAC will use them.
    - **Configure Bindings** _(optional)_: create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to control which users see the macmon NAC application on the **My Applications** page.

3. Click **Submit**.

### Download the signing certificate

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click on the name of the newly created macmon NAC provider.
3. Click **Download** under **Download signing certificate**. The contents of this certificate will be required in the next section.

## macmon configuration

1. Log in to the macmon NAC administrative console.
2. Navigate to **Settings** > **Identity Stores** and click **Create**.
3. Configure the following settings:
    - **Name**: `authentik` (or another descriptive label).
    - **SP Host name**: `macmon.company`.
    - **SP Entity ID**: `https://macmon.company/login/?acs`.
    - **IdP Issuer (Entity ID)**: `https://authentik.company/application/saml/<application_slug>/metadata/`.
    - **IdP certificate**: paste the contents of the authentik signing certificate, removing the `-----BEGIN CERTIFICATE-----` and `-----END CERTIFICATE-----` lines.
    - **IdP SSO URL**: `https://authentik.company/application/saml/<application_slug>/sso/binding/init/`.
    - **Name ID format**: `E-mail address`.
4. Save the identity store configuration.

:::info User Provisioning
macmon NAC provisions new users automatically when they authenticate through SSO. Newly created accounts have no policies by default, so they cannot access resources until an administrator assigns groups/permissions or you configure automated policy assignments. Designing those policies is outside the scope of this guide. You can review these accounts in macmon NAC under **Users** > **User Accounts** > **External user accounts** and filter by the identity store name you configured earlier.
:::

## Configuration verification

To confirm that authentik is properly configured with macmon NAC, log out of Amazon Business. On the macmon NAC portal select **Single Sign-On**. You should be redirected to authentik to login, and if successful, you should then be redirected to the macmon NAC interface.
