---
title: Integrate with YouTrack
sidebar_label: YouTrack
support_level: community
---

## What is YouTrack

> YouTrack is a proprietary, commercial browser-based bug tracker, issue tracking system, and project management software developed by JetBrains.
>
> -- https://www.jetbrains.com/youtrack/

## Preparation

The following placeholders are used in this guide:

- `youtrack.company` is the FQDN of the YouTrack installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of YouTrack with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **SAML Provider** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Take note of the **slug** value as it will be required later.
    - Set the **ACS URL** to `https://placeholder.com`.
    - Set the **Entity ID** to `https://youtrack.company/admin/hub/`.
    - Set the **Service Provider Binding** to `Post`.
    - Under **Advanced protocol settings**, set an available signing key and make sure **Sign assertions** is toggled.
    - Then, also under **Advanced protocol settings**, make sure **NameID Property Mapping** is set to `authentik default SAML Mapping: username`. Make sure the [Allow users to change username](https://docs.goauthentik.io/docs/sys-mgmt/settings#allow-users-to-change-username) setting is disabled to prevent authentication issues.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

### Get the certificate's SHA-256 fingerprint

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **System** > **Certificates**, expand the certificate chosen in the previous section, and take note of the **Certificate Fingerprint (SHA256)**.

## YouTrack configuration

1. To integrate YouTrack with authentik, log in as a _Low-level Admin or higher_, click the **Administration** cog near the bottom of the page, hover over **Access Management**, and then select **Auth Modules**.
2. Click **New module**, then select **SAML 2.0**.
3. Fill out the form with the following information:
    - **Name**: Set an appropriate name (e.g. `authentik`)
    - **SAML SSO URL**: `https://authentik.company/application/saml/<application slug>/sso/binding/redirect/`
    - **IdP entity ID**: `https://youtrack.company/admin/hub/`
    - **Certificate fingerprint**: Set to the SHA-256 fingerprint retrieved in the previous step.
4. Click **Create** to submit the form and take note of the **ACS URL**.

### Update the authentik provider

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** > **_Application Name_**, then click **Edit**.
3. Replace the placeholder value for the **ACS URL** with the value copied from the previous section.

## Resources

- [YouTrack SAML 2.0 Auth Module Documentation](https://www.jetbrains.com/help/youtrack/server/saml-authentication-module.html)

## Configuration verification

To confirm that authentik is properly configured with YouTrack, log out and attempt to log back in. You should be redirected to authentik to complete authentication.
