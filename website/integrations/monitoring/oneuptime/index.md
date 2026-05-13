---
title: Integrate with OneUptime
sidebar_label: OneUptime
support_level: community
---

## What is OneUptime?

> OneUptime is an open-source observability and incident management platform that provides infrastructure monitoring, incident management, status pages, and APM.
>
> -- https://oneuptime.com/

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.
- `oneuptime.company` is the FQDN of your OneUptime installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

:::warning
Configuring SSO with OneUptime Cloud requires a Scale plan or higher. If you are self-hosting OneUptime, SSO is available on all instances at no cost.
:::

## Download the signing certificate from authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **System** > **Certificates**.
3. Select the certificate that you want to use for signing.
4. Click **Download** to save the public certificate to your machine.

## Create the initial SSO configuration in OneUptime

:::info Algorithm support
OneUptime currently supports the RSA-based SAML signature methods `RSA-SHA1`, `RSA-SHA256`, `RSA-SHA384`, and `RSA-SHA512`, plus the digest methods `SHA1`, `SHA256`, `SHA384`, and `SHA512`. It does not support ECDSA-based SAML signature methods.
:::

1. Log in to OneUptime as an administrator.
2. Navigate to **Project Settings** > **Authentication** > **SSO**.
3. Click **Create SSO** and configure the following settings:
    - **Name**: enter a descriptive name, such as `authentik`.
    - **Sign On URL**: set to `https://authentik.company/application/saml/<application_slug>/`.
    - **Issuer**: set to `https://authentik.company/application/saml/<application_slug>/metadata/`.
    - **Public Certificate**: paste the certificate that you downloaded from authentik, including the `BEGIN CERTIFICATE` and `END CERTIFICATE` lines.
    - **Signature Method**: select `RSA-SHA256`.
    - **Digest Method**: select `SHA256`.
4. Save the configuration.
5. Click **View SSO Config** on the new SSO entry.
6. Note the following values:
    - **Identifier (Entity ID)**
    - **Reply URL (Assertion Consumer Service URL)**

## Create an application and provider in authentik

To support the integration of OneUptime with authentik, you need an application/provider pair in authentik that uses the values provided by OneUptime.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **slug** value because you will use it when you return to OneUptime.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations:
        - Set the **ACS URL** to the **Reply URL (Assertion Consumer Service URL)** from OneUptime.
        - Set the **Audience** to the **Identifier (Entity ID)** from OneUptime.
        - Under **Advanced protocol settings**:
            - Set the **Signing Certificate** to the same certificate that you downloaded earlier.
            - Set **NameID Property Mapping** to `authentik default SAML Mapping: Email`.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.
3. Click **Submit** to save the new application and provider.

:::info NameID mapping
OneUptime uses the SAML NameID as the user email address. Setting the authentik **NameID Property Mapping** to `authentik default SAML Mapping: Email` ensures that users can sign in successfully.
:::

:::info Role mapping
OneUptime does not currently support SAML role mapping. Configure user roles separately in OneUptime after users sign in.
:::

## Configuration verification

To confirm that authentik is properly configured with OneUptime, log out of OneUptime and open the login page in a private or incognito browser window. Start the SSO sign-in flow, enter an email address for a user who should have access, and confirm that you are redirected to authentik for authentication and then back to OneUptime.

## Resources

- [OneUptime SSO documentation](https://github.com/OneUptime/oneuptime/blob/master/App/FeatureSet/Docs/Content/identity/sso.md)
