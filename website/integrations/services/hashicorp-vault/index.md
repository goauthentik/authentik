---
title: Hashicorp Vault
---

<span class="badge badge--primary">Support level: authentik</span>

## What is Vault

From https://vaultproject.io

:::note
Secure, store and tightly control access to tokens, passwords, certificates, encryption keys for protecting secrets and other sensitive data using a UI, CLI, or HTTP API.
:::

:::note
This is based on authentik 2022.2.1 and Vault 1.9.3. Instructions may differ between versions. This guide does not cover vault policies. See https://learn.hashicorp.com/tutorials/vault/oidc-auth?in=vault/auth-methods for a more in depth vault guide
:::

## Preparation

The following placeholders will be used:

-   `authentik.company` is the FQDN of authentik.
-   `vault.company` is the FQDN of Vault.

### Step 1

In authentik, create an _OAuth2/OpenID Provider_ (under _Applications/Providers_) with these settings:

:::note
Only settings that have been modified from default have been listed.
:::

**Protocol Settings**

-   Name: Vault
-   Signing Key: Select any available key

-   Redirect URIs/Origins:

```
https://vault.company/ui/vault/auth/oidc/oidc/callback
https://vault.company/oidc/callback
http://localhost:8250/oidc/callback
```

:::note
Take note of the `Client ID` and `Client Secret`, you'll need to give them to Vault in _Step 3_.
:::

### Step 2

In authentik, create an application (under _Resources/Applications_) which uses this provider. Optionally apply access restrictions to the application using policy bindings.

:::note
Only settings that have been modified from default have been listed.
:::

-   Name: Vault
-   Slug: vault-slug
-   Provider: Vault

### Step 3

Enable the oidc auth method
`vault auth enable oidc`

Configure the oidc auth method, oidc discovery url is the OpenID Configuration Issuer in your provider

```
vault write auth/oidc/config \
         oidc_discovery_url="https://authentik.company/application/o/vault-slug/" \
         oidc_client_id="Client ID" \
         oidc_client_secret="Client Secret" \
         default_role="reader"
```

Create the reader role

```
vault write auth/oidc/role/reader \
      bound_audiences="Client ID" \
      allowed_redirect_uris="https://vault.company/ui/vault/auth/oidc/oidc/callback" \
      allowed_redirect_uris="https://vault.company/oidc/callback" \
      allowed_redirect_uris="http://localhost:8250/oidc/callback" \
      user_claim="sub" \
      policies="reader"
```

You should then be able to sign in via OIDC
`vault login -method=oidc role="reader"`
