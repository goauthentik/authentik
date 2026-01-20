---
title: Keycloak
tags:
    - source
    - keycloak
    - saml
---

Allows users to authenticate using their Keycloak credentials by configuring Keycloak as a federated identity provider via SAML.

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.
- `keycloak.company` is the FQDN of the Keycloak installation.

## Export certificates

Before configuring either service, you need to export the signing certificates from both Keycloak and authentik. Each service needs the other's public certificate to verify signatures and handle SAML encryption.

### Export the Keycloak signing certificate

1. Log in to Keycloak as an administrator.
2. Navigate to **Realm settings** > **Keys**.
3. Find the RSA key with **Use** set to `SIG`.
4. Click **Certificate** to copy the certificate value.
5. Save the certificate in the following format:

```
-----BEGIN CERTIFICATE-----
<Copied Keycloak Public Key Certificate Content>
-----END CERTIFICATE-----
```

### Export the authentik signing certificate

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **System** > **Certificates**.
3. Click on the certificate you plan to use for signing (e.g., the default `authentik Self-signed Certificate`).
4. Click **Download Certificate** to download the public certificate file.

## Keycloak configuration

### Create a SAML client in Keycloak

1. Log in to Keycloak as an administrator.
2. Navigate to **Clients** and click **Create client**.
3. Configure the client with the following settings:
    - Set **Client type** to `SAML`.
    - Set **Client ID** to `https://authentik.company/source/saml/keycloak/metadata/`.
4. Click **Next**.
5. Configure the following settings:
    - Set **Valid redirect URIs** to `https://authentik.company/source/saml/keycloak/acs/`.
    - Set **Master SAML Processing URL** to `https://authentik.company/source/saml/keycloak/acs/`.
    - Set **Root URL** to `https://authentik.company`.
6. Click **Save**.

### Configure signing and encryption

1. Navigate to the **Settings** tab and scroll to **Signature and Encryption**.
2. Configure the following settings:
    - Enable **Sign documents**.
    - Enable **Sign assertions**.
    - Enable **Encrypt assertions** (optional, for encrypted SAML).

### Upload the authentik certificate to Keycloak

1. In the client settings, navigate to the **Keys** tab.
2. Configure the following settings:
    - Enable **Client signature required** if you want Keycloak to verify signatures from authentik.
    - Click **Import** and upload the authentik certificate you exported earlier. This allows Keycloak to verify signatures on requests from authentik.
    - If encryption is enabled, click **Import** under the encryption key and upload the authentik certificate.

## authentik configuration

### Upload the Keycloak certificate to authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **System** > **Certificates** and click **Import**.
3. Give it a name like `Keycloak Signing Certificate`.
4. Paste the Keycloak certificate you exported earlier into the **Certificate** field.
5. Leave the **Private Key** field empty.
6. Click **Create**.

### Create a SAML source in authentik

1. Navigate to **Directory** > **Federation and Social login** and click **Create**.
2. Select **SAML Source** and configure the following settings:
    - Set **Name** to `Keycloak`.
    - Set **Slug** to `keycloak`.
    - Set **SSO URL** to `https://keycloak.company/realms/<realm-name>/protocol/saml`.
    - Set **SLO URL** to `https://keycloak.company/realms/<realm-name>/protocol/saml`.
    - Set **Issuer** to `https://authentik.company/source/saml/keycloak/metadata/`.
    - Set **Service Provider Binding** to `Post (Auto-Submit)`.
    - Set **Signing Keypair** to an authentik certificate (e.g., the default self-signed certificate).
    - Set **Verification Certificate** to the Keycloak certificate you uploaded earlier.
    - Enable **Verify assertion signature**.
    - Enable **Verify response signature**.
    - Set **Encryption Certificate** to an authentik certificate if you enabled encryption in Keycloak.
3. Click **Finish**.

:::info Display new source on login screen
For instructions on how to display the new source on the authentik login page, refer to the [Add sources to default login page documentation](../../index.md#add-sources-to-default-login-page).
:::

:::info Embed new source in flow :ak-enterprise
For instructions on embedding the new source within a flow, such as an authorization flow, refer to the [Source Stage documentation](../../../../../add-secure-apps/flows-stages/stages/source).
:::

## Troubleshooting

- **Signature verification failed**: Ensure the correct certificates are configured on both sides. Each side needs the other's signing certificate for verification.
- **Encryption errors**: Ensure the encrypting party has the other party's public certificate, and the decrypting party has their own private key.

## Resources

- [Keycloak Docs — Creating a SAML Client](https://www.keycloak.org/docs/latest/server_admin/index.html#_client-saml-configuration)
- [Keycloak Docs — Configuring Realms](https://www.keycloak.org/docs/latest/server_admin/index.html#_configuring-realms)
