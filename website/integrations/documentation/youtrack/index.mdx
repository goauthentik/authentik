---
title: Integrate with YouTrack
sidebar_label: YouTrack
support_level: community
---

import SAMLProvider20265Warning from "../../\_saml-provider-2026-5-warning.mdx";

## What is YouTrack?

> YouTrack is a project management and team collaboration tool for tracking tasks, managing projects, maintaining knowledge bases, supporting customers, and collaborating across teams.
>
> -- https://www.jetbrains.com/youtrack/

## Preparation

The following placeholders are used in this guide:

- `youtrack.company` is the FQDN of the YouTrack installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of YouTrack with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

<SAMLProvider20265Warning />

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **Slug** value because it is required later.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Temporarily set the **ACS URL** and **Audience** to `https://temp.temp`.
        - Under **Advanced protocol settings**:
            - Select an available **Signing Certificate**.
            - Enable **Sign assertions**.
            - Set **NameID Property Mapping** to `authentik default SAML Mapping: Username`. Make sure that the [Allow users to change username](/docs/sys-mgmt/settings#allow-users-to-change-username) setting is disabled to prevent authentication issues.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

### Get the certificate fingerprint

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **System** > **Certificates** and expand the certificate that you selected in the previous section.
3. Take note of the **Certificate Fingerprint (SHA256)**. This value is required in the next section.

## YouTrack configuration

1. Log in to YouTrack as a Low-level Admin or higher.
2. Click the **Administration** cog near the bottom of the page, hover over **Access Management**, and then select **Auth Modules**.
3. Click **New module**, then select **SAML 2.0**.
4. Fill out the form with the following information:
    - **Name**: set a descriptive name, such as `authentik`.
    - **SAML SSO URL**: `https://authentik.company/application/saml/<application_slug>/`
    - **IdP entity ID**: `https://authentik.company/application/saml/<application_slug>/metadata/`
    - **Certificate fingerprint**: enter the **Certificate Fingerprint (SHA256)** value from authentik.
5. Click **Finish** to create the module.
6. Take note of the **ACS URL** and **SP entity ID** values that YouTrack generates. These values are required in the next section.
7. Click **Save** to apply the settings.
8. Click **Enable** to enable the module.

### Update the authentik provider

1. Return to the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and open the SAML provider that you created earlier.
3. Under **Protocol settings**, set the following values:
    - **ACS URL**: set to the **ACS URL** value from YouTrack.
    - **Audience**: set to the **SP entity ID** value from YouTrack.
4. Click **Update** to save the provider.
5. Return to the YouTrack SAML 2.0 auth module and click **Test login**. YouTrack should redirect you to authentik for authentication and then back to YouTrack.

## Configuration verification

To confirm that authentik is properly configured with YouTrack, log out of YouTrack and sign in with the SAML 2.0 auth module. You should be redirected to authentik and, after authenticating, returned to YouTrack.

## Resources

- [YouTrack Server Documentation - SAML 2.0 Auth Module](https://www.jetbrains.com/help/youtrack/server/saml-authentication-module.html)
