---
title: Integrate with Semgrep
sidebar_label: Semgrep
support_level: community
---

## What is Semgrep?

> Semgrep AppSec Platform helps teams find, triage, and manage code, dependency, and secrets findings across repositories and developer workflows.
>
> -- https://semgrep.dev

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.
- `some.company` is the email domain used by users who sign in to Semgrep.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Semgrep with authentik, you need to create several property mappings and an application/provider pair in authentik.

### Create property mappings

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**. Create the following **SAML Provider Property Mapping**s:
    - **ID Mapping:**
        - **Name**: `semgrep-id`
        - **SAML Attribute Name**: `id`
        - **Expression**: `return request.user.email`
    - **Email Mapping:**
        - **Name**: `semgrep-email`
        - **SAML Attribute Name**: `email`
        - **Expression**: `return request.user.email`
    - **Name Mapping:**
        - **Name**: `semgrep-name`
        - **SAML Attribute Name**: `name`
        - **Expression**: `return request.user.name`
    - **First Name Mapping:**
        - **Name**: `semgrep-first-name`
        - **SAML Attribute Name**: `firstName`
        - **Expression**: `return request.user.name.split(" ", 1)[0] if request.user.name else request.user.username`
    - **Last Name Mapping:**
        - **Name**: `semgrep-last-name`
        - **SAML Attribute Name**: `lastName`
        - **Expression**: `return request.user.name.rsplit(" ", 1)[-1] if " " in request.user.name else ""`

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations:
        - Set the **ACS URL** to `https://temp.temp`.
        - Set the **Audience** to `https://temp.temp`.
        - Under **Advanced protocol settings**:
            - Select an available **Signing Certificate**.
            - Add the five **Property mappings** that you created in the previous section.
            - Set **NameID Property Mapping** to `semgrep-email`.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Create Application** to save the new application and provider.

## Semgrep configuration

1. Log in to [Semgrep AppSec Platform](https://semgrep.dev/login) as an administrator.
2. Navigate to **Settings** > **Access** > **Login methods**.
3. In the **Single sign-on (SSO)** section, set **Email domain** to `some.company` and click **Initialize**.
4. In the **Configure Single Sign-On** dialog, select **Custom SAML**.
5. When Semgrep shows the service provider values, copy the following values and keep this window open:
    - **SSO URL**
    - **Audience URL (SP Entity ID)**

## Configure the remaining information in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click the provider that you created in the previous step.
3. Click **Edit**.
4. Under **Protocol settings**, set the value of the **ACS URL** to the **SSO URL** value from Semgrep. Then, set the value of the **Audience** to the **Audience URL (SP Entity ID)** value from Semgrep.
5. Click **Update**.

## Enable SSO in Semgrep

1. In Semgrep AppSec Platform, continue through the **Configure Single Sign-On** dialog.
2. When prompted for authentik's identity provider details, enter the following values:
    - **IdP SSO URL**: `https://authentik.company/application/saml/<application_slug>/`
    - **IdP Issuer ID**: `https://authentik.company/application/saml/<application_slug>/metadata/`
    - **Upload/paste certificate**: from the authentik SAML provider page, under **Related objects** > **Download signing certificate**, click **Download** and upload the downloaded certificate.
3. Follow Semgrep's prompts to test the SAML sign-in flow.
4. After the test succeeds, close the test page, confirm the connection details, and finish the setup.
5. Confirm that the connection status is active under **Settings** > **Access** > **Login methods**.

## Configuration verification

To confirm that authentik is properly configured with Semgrep, log out of Semgrep and open the Semgrep login page in a private or incognito browser window. Start the SSO sign-in flow, enter an email address for the domain you configured, and confirm that you are redirected to authentik for authentication and then back to Semgrep.

## Resources

- [Semgrep Docs - SSO authentication](https://semgrep.dev/docs/deployment/sso)
- [Semgrep Docs - SAML SSO with Google Workspace](https://semgrep.dev/docs/kb/semgrep-appsec-platform/saml-google-workspace)
