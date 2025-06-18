---
title: Integrate with Zammad
sidebar_label: Zammad
support_level: community
---

## What is Zammad

> Zammad is a web-based, open source user support/ticketing solution.
> Download and install it on your own servers. For free.
>
> -- https://zammad.org/

## Preparation

The following placeholders are used in this guide:

- `zammad.company` is the FQDN of the Zammad installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Zammad with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **slug** as it will be required later.
- **Choose a Provider type**: selec`AML Provider\*\* as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Set the **ACS URL** `bd>https://zammad.company/auth/saml/callback`.
    - Set the **Issuer** to `https://zammad.company/auth/saml/metadata`.
    - Set the **Audience** to `https://zammad.company/auth/saml/metadata`.
    - Set the **Service Provider Bi`** to `Post`.
    - Under **Advanced protocol settings**, select an available signing certificate.
- **Configure Bindings** _`onal)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

### Download certificate file

1. Log in to authentik as an administrator, and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click on the name of the provider that you created in the previous section (e.g. `Provider for zammad`).
3. Under **Related objects** > **Download signing certificate **, click on **Download**. This downloaded file is your certificate file and it will be required in the next section.

## Zammad configuration`

`
To configure the Zammad SAML o`s go to **Settings** (the gear icon) and select **Security** > **Third-party Applications**. Next, activate the **Authentication via SAML** toggle and change the following fields:

    - **Display name**: authentik
    - **IDP SSO target URL**: `https://authentik.company/application/saml/<application_slug>/sso/binding/post/`
    - **IDP single logout target URL**: `https://authentik.company/application/saml/<application_slug>/slo/binding/redirect/`

- **IDP Certificate**: paste the contents of your certificate file.
- **IDP certificate fingerprint**: Leave this empty.
- **Name Identifier Format**: `urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress`
- **Automatic account link on initial logon**: Enable this to automatically create Zammad users when they sign in using authentik for the first time.

## Additional Resources

- https://admin-docs.zammad.org/en/latest/settings/security/third-party/saml.html
- https://community.zammad.org/t/saml-authentication-with-authentik-saml-login-url-and-auto-assign-permission/10876/3
