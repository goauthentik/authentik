---
title: Shibboleth
tags:
    - source
    - shibboleth
    - saml
---

Allows users to authenticate using their Shibboleth credentials by configuring Shibboleth as a federated identity provider via SAML.

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.
- `shibboleth.company` is the FQDN of the Shibboleth IdP installation.
- `shibboleth-slug` is the slug you will assign to the SAML source in authentik (e.g., `shibboleth`).

## authentik configuration

### Create a SAML source in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login** and click **Create**.
3. Select **SAML Source** and configure the following settings:
    - Set **Name** to `Shibboleth`.
    - Set **Slug** to `shibboleth` (must match the slug used in Shibboleth's metadata configuration).
    - Set **SSO URL** to `https://shibboleth.company/idp/profile/SAML2/Redirect/SSO`.
    - Set **Service Provider Binding** to `Redirect`.
    - Set **Issuer** to `https://authentik.company/source/saml/<shibboleth-slug>/metadata/`.
    - Set **NameID Policy** to `Transient`.
      :::warning NameID Policy
      Shibboleth supports the `Transient` NameID by default. You will need to reconfigure shibboleth to use other NameIDs.
      :::
    - Set **Signing Keypair** to an authentik certificate (e.g., the default `authentik Self-signed Certificate`).
    - Set **Encryption Certificate** to an authentik certificate (e.g., the default `authentik Self-signed Certificate`).
4. Click **Finish**.

:::info Display new source on login screen
For instructions on how to display the new source on the authentik login page, refer to the [Add sources to default login page documentation](../../index.md#add-sources-to-default-login-page).
:::

:::info Embed new source in flow :ak-enterprise
For instructions on embedding the new source within a flow, such as an authorization flow, refer to the [Source Stage documentation](../../../../../add-secure-apps/flows-stages/stages/source).
:::

## Shibboleth configuration

### Add authentik as a Service Provider

1. Edit `/opt/shibboleth-idp/conf/metadata-providers.xml` on the Shibboleth IdP server.
2. Add the following `MetadataProvider` element before the final closing tag of the existing `MetadataProvider` block:

```xml
<MetadataProvider id="Authentik"
                  xsi:type="FileBackedHTTPMetadataProvider"
                  backingFile="%{idp.home}/metadata/authentik-metadata.xml"
                  metadataURL="https://authentik.company/source/saml/<shibboleth-slug>/metadata/" />
```

3. Restart the Shibboleth IdP to apply the changes.

## Resources

- [Shibboleth IdP Documentation](https://shibboleth.atlassian.net/wiki/spaces/IDP5/overview)
