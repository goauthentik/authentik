---
title: Integrate with AppFlowy
sidebar_label: AppFlowy
support_level: community
---

## What is AppFlowy

> AppFlowy is an open-source workspace collaboration platform (similar to Notion) that lets teams create, manage, and collaborate on documents, databases, and projects.
> 
> -- https://appflowy.com

## Preparation

The following placeholders are used in this guide:

- `appflowy.company` is the FQDN of the AppFlowy installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of AppFlowy with authentik, you need to create a certificate and an application/provider pair in authentik.

### Create a certificate-key pair

1. Log in to authentik as an administrator and open the authentik Admin interface. 
2. Navigate to **System** > **Certificates** and click **Generate**.
3. Set the following required fields:
   - **Common name**: set an appropriate name (For example: `AppFlowyCertSAML`).
   - **Validity days**: set an appropriate certificate validity period (or keep the default value of `365`).
   - **Private key algorithm**: `RSA`
4. Click **Generate** and take note of the **Certificate** and **Private key** values as they will be required later on.

### Create an application and provider in authentik

1. Log in to authentik as an administrator, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - **ACS URL**: `https://appflowy.company/gotrue/sso/saml/acs`
        - **Issuer**: `authentik`
        - **Service Provider Binding**: `Post`
        - **Audience**: `https://appflowy.company/gotrue/sso/saml/metadata`
        - Under **Advanced protocol settings**:
            - **Signing certificate**: select the certificate created earlier
            - **Sign assertions**: enabled
            - **Sign responses**: enabled
            - **Verification certificate**: select the same certificate
            - **NameID Property Mapping**: `authentik default SAML Mapping: Email`
            - **Default relay state**: `https://appflowy.company/auth/callback`
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.
3. Click **Submit** to create the application and provider.

## AppFlowy configuration

Configure AppFlowy Cloud to use authentik as its SAML IdP.

### Convert the certificate and private key

AppFlowy requires the private key in PKCS#1 and base64 (single-line) format.

1. Convert the private key to PKCS#1 (the `-traditional` flag is required with recent OpenSSL versions):
   ```bash
   openssl rsa -in AppFlowyCertSAML_private_key.pem -traditional -out key_pkcs1.pem
   ```
2. Convert the PKCS#1 private key to a single-line base64 string:
   ```bash
   sed -n '/^-----BEGIN RSA PRIVATE KEY-----$/,/^-----END RSA PRIVATE KEY-----$/p' key_pkcs1.pem      | grep -v '^-----'      | tr -d '\n'
   ```
   Copy this output for `GOTRUE_SAML_PRIVATE_KEY`.
3. Convert the certificate to a single-line format with `\n` escapes:
   ```bash
   awk 'NF {sub(/\r/, ""); printf "%s\\n",$0}' AppFlowyCertSAML_certificate.pem
   ```
   Copy this output for `AUTH_SAML_CERT`.

### Configure the `.env` file in AppFlowy

In the AppFlowy root installation directory, update the `.env` file:

```bash
AUTH_SAML_ENABLED=true
GOTRUE_SAML_ENABLED=true

# Paste the SSO URL (POST binding) from authentik's "Provider for AppFlowy"
AUTH_SAML_ENTRY_POINT="https://authentik.company/application/saml/appflowy/sso/binding/post"

AUTH_SAML_ISSUER="authentik"
AUTH_SAML_CALLBACK_URL="https://appflowy.company/gotrue/sso/saml/acs"
AUTH_SAML_DEFAULT_REDIRECT_URL="https://appflowy.company/app"

# From the conversion steps above
GOTRUE_SAML_PRIVATE_KEY="<Base64 private key (single line)>"
AUTH_SAML_CERT="<Certificate with \\n escapes (single line)>"
```

:::note
Ensure `GOTRUE_DISABLE_SIGNUP=false` so first-time SAML users can sign in.
:::

Restart the AppFlowy services.

### Configure SAML SSO in the AppFlowy Admin Dashboard

1. In authentik, open **Applications → Providers → Provider for AppFlowy**.
2. Under **Metadata related objects**, copy the **download URL** (metadata URL).
3. Open the AppFlowy Admin Console at `https://appflowy.company/console` and sign in.
4. Go to **Admin → Create SSO**.
5. Paste the **Metadata URL** from authentik.
6. Click **Create**.

## Configuration verification

To confirm that authentik is properly configured with AppFlowy, log out and then log back in by selecting the **AppFlowy** application from the authentik User interface. You should be automatically redirected and signed in to AppFlowy.

## Resources

- [AppFlowy Documentation - How to login using Okta SAML 2.0](https://appflowy.com/docs/How-to-log-in-using-Okta-SAML-2)
- [AppFlowy Documentation - How to login using SAML 2.0](https://appflowy.com/docs/How-to-log-in-using-SAML-2)
