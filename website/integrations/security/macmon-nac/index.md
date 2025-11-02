---
title: Integrate with macmon NAC
sidebar_label: macmon NAC
support_level: community
---

## What is macmon NAC

> macmon NAC is a network access control platform that provides visibility, policy enforcement, and automated responses for devices connecting to your network.
>
> -- https://macmon.eu

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.
- `macmon.company` is the FQDN of your macmon NAC environment.

:::info
This documentation lists only the settings that you need to change from their default values. Changing settings not mentioned in this guide can prevent single sign-on from working correctly.
:::

## authentik configuration

Create a SAML application and provider in authentik to issue assertions that match the macmon NAC requirements.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (You can also create them separately and connect the provider to the application afterward.)

- **Application**: provide a descriptive name such as `macmon NAC`, optionally assign a group, choose a policy engine mode, and configure any UI settings. Record the **slug** because macmon NAC requires it in the identity store URLs.
- **Choose a Provider type**: select **SAML Provider**.
- **Configure the Provider**:
    - Provide a name (or accept the auto-generated value) and select the authorization flow to use.
    - Set the **ACS URL** to `https://macmon.company/login/?acs`.
    - Set the **Issuer** to `https://macmon.company`.
    - Set the **Service Provider Binding** to `Post`.
    - Under **Advanced protocol settings**, choose any available certificate as the **Signing Certificate**, enable **Sign Assertions**, and enable **Sign Responses**.
    - Set **NameID Property Mapping** to the email mapping you selected (for example, `authentik default SAML Mapping: Email`). macmon NAC expects the NameID format `E-mail address`, so ensure the chosen mapping provides the user’s email. You can optionally add mappings for additional claims such as `firstName`, `surName`, `memberOf`, or `description` if macmon NAC will consume them.
- **Configure Bindings** _(optional)_: create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to control which users see the macmon NAC application on the **My Applications** page.

3. Click **Submit** to save the application and provider.

## macmon configuration

1. Log in to the macmon NAC administrative console.
2. Navigate to **Settings** > **Identity Stores** and click **Create**.
3. Complete the new identity store form with the following values:
    - **Name**: `authentik` (or another descriptive label).
    - **SP Host name**: `macmon.company`.
    - **SP Entity ID**: `https://macmon.company/login/?acs`.
    - **IdP Issuer (Entity ID)**: `https://authentik.company/application/saml/<application_slug>/metadata/`.
    - **IdP certificate**: paste the authentik signing certificate used for this integration, removing the `-----BEGIN CERTIFICATE-----` and `-----END CERTIFICATE-----` lines.
    - **IdP SSO URL**: `https://authentik.company/application/saml/<application_slug>/sso/binding/init/`.
    - **Name ID format**: `E-mail address`.
4. Save the identity store configuration.

:::note
macmon NAC provisions new users automatically when they authenticate through SSO. Newly created accounts have no policies by default, so they cannot access resources until an administrator assigns groups/permissions or you configure automated policy assignments. Designing those policies is outside the scope of this guide. You can review these accounts under **Users** > **User Accounts** > **External user accounts** in macmon and filter by the identity store name you configured earlier.
:::

## Configuration verification

1. Open a new browser session (or private window) and browse to the macmon NAC portal.
2. Click **Single Sign-On**.
3. Confirm that you are redirected to authentik for authentication. Sign in with an account allowed to access macmon NAC.
4. After successful authentication, verify that you are returned to the macmon NAC interface without additional prompts.
