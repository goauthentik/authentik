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

### Create property mappings

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**. Create two **SAML Provider Property Mapping**s with the following settings:
    - **Name Mapping:**
        - **Name**: Choose a descriptive name
        - **SAML Attribute Name**: <kbd>name</kbd>
        - **Friendly Name**: Leave blank
        - **Expression**: <kbd>return request.user.name</kbd>
    - **Email Mapping:**
        - **Name**: Choose a descriptive name
        - **SAML Attribute Name**: <kbd>email</kbd>
        - **Friendly Name**: Leave blank
        - **Expression**: <kbd>return request.user.email</kbd>

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **slug** as it will be required later.
- **Choose a Provider type**: select **SAML Provider** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Set the **ACS URL** to <kbd>https://<em>zammad.company</em>/auth/saml/callback</kbd>.
    - Set the **Issuer** to <kbd>https://<em>zammad.company</em>/auth/saml/metadata</kbd>.
    - Set the **Audience** to <kbd>https://<em>zammad.company</em>/auth/saml/metadata</kbd>.
    - Set the **Service Provider Binding** to `Post`.
    - Under **Advanced protocol settings**
      - Add the two **Property Mappings** you created in the previous section
      - Set the **NameID Property Mapping** to the name property mapping created in the previous section
      - Select your Signing Certificate (the default is named `authentik Self-signed Certificate`)
      - Be sure **Sign assertions** is active
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## zammad Setup

Configure Zammad SAML settings by going to settings (the gear icon), and selecting `Security -> Third-party Applications` and activate `Authentication via SAML` and change the following fields:

- Display name: authentik
- IDP SSO target URL: https://authentik.company/application/saml/zammad/sso/binding/post/
- IDP single logout target URL: https://authentik.company/application/saml/zammad/slo/binding/redirect/
- Download your IDP certificate from https://authentik.company/if/admin/#/crypto/certificates
  - Copy the entire contents into the IDP certificate box, including the `----BEGIN CERTIFICATE----` and `----END CERTIFICATE----` lines
- IDP certificate fingerprint: empty
- Name Identifier Format: <kbd>urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress</kbd>
- If you want Zammad users to be created automatically the first time the sign in via Authentik, activate the **Automatic account link on initial logon** option 

## Additional Resources

- https://admin-docs.zammad.org/en/latest/settings/security/third-party/saml.html
- https://community.zammad.org/t/saml-authentication-with-authentik-saml-login-url-and-auto-assign-permission/10876/3
