---
title: Integrate with OneUptime
sidebar_label: OneUptime
support_level: community
---

import SAMLProvider20265Warning from "../../\_saml-provider-2026-5-warning.mdx";

## What is OneUptime?

> OneUptime is an open-source observability and incident management platform that provides infrastructure monitoring, incident management, status pages, and APM.
>
> -- https://oneuptime.com/

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

:::warning OneUptime Cloud requirement
Configuring SSO with OneUptime Cloud requires a Scale plan or higher. If you are self-hosting OneUptime, SSO is available on all instances at no cost.
:::

## authentik configuration

To support the integration of OneUptime with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

<SAMLProvider20265Warning />

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **Slug** value because you will use it when you configure OneUptime.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set the **ACS URL** to `https://temp.temp`. You will replace this after OneUptime provides the real Reply URL.
        - Set the **Audience** to `https://temp.temp`. You will replace this after OneUptime provides the real Identifier.
        - Under **Advanced protocol settings**:
            - Select an available **Signing Certificate**.
            - Set **NameID Property Mapping** to `authentik default SAML Mapping: Email`.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

### Download the signing certificate

1. Navigate to **Applications** > **Providers** and click on the name of the SAML provider that you created for OneUptime.
2. Under **Related objects** > **Download signing certificate**, click **Download**. You need this certificate file in the next section.

## OneUptime configuration

### Create an SSO configuration

1. Log in to OneUptime as an administrator.
2. Navigate to **Project Settings** > **Authentication** > **SSO**.
3. Click **Create SSO** and configure the following settings:
    - **Name**: enter a descriptive name.
    - **Description**: enter a description.
    - **Sign On URL**: `https://authentik.company/application/saml/<application_slug>/`
    - **Issuer**: `https://authentik.company/application/saml/<application_slug>/metadata/`
    - **Public Certificate**: paste the certificate that you downloaded from authentik, including the `BEGIN CERTIFICATE` and `END CERTIFICATE` lines.
    - **Signature Method**: `RSA-SHA256`
    - **Digest Method**: `SHA256`
    - **Enabled**: enable the SSO configuration when you are ready to test it.
    - **Teams**: select the OneUptime teams that newly signed-in users should be added to.
4. Save the configuration.
5. Click **View SSO Config** on the new SSO entry.
6. Note the following values:
    - **Identifier (Entity ID)**
    - **Reply URL (Assertion Consumer Service URL)**

OneUptime does not support SAML role mapping. Manage SSO user access with the teams that you select on the OneUptime SSO configuration, and configure any additional user permissions in OneUptime.

### Update the authentik provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and open the SAML provider that you created for OneUptime.
3. Update the provider with the values from OneUptime:
    - **ACS URL**: set to the OneUptime **Reply URL (Assertion Consumer Service URL)**.
    - **Audience**: set to the OneUptime **Identifier (Entity ID)**.
4. Click **Update**.

After you verify that SSO works, you can open **Project Settings** > **Authentication** > **SSO** in OneUptime and enable **Force SSO for Login**.

## Configuration verification

To confirm that authentik is properly configured with OneUptime, open the OneUptime integration from the authentik Application Dashboard. You should be redirected to authentik for authentication and then signed in to OneUptime.

You can also test the SP-initiated flow by opening the OneUptime login page in a private or incognito browser window, starting the SSO sign-in flow, and entering the email address of a user who should have access. You should be redirected to authentik for authentication and then back to OneUptime.

## Resources

- [OneUptime Docs - SSO](https://oneuptime.com/docs/en/identity/sso)
- [OneUptime pricing](https://oneuptime.com/pricing)
