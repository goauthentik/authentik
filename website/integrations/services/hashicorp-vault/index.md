---
title: Integrate with Hashicorp Vault
sidebar_label: Hashicorp Vault
---

# Integrate with Hashicorp Vault

<span class="badge badge--primary">Support level: authentik</span>

## What is Vault

> Secure, store and tightly control access to tokens, passwords, certificates, encryption keys for protecting secrets and other sensitive data using a UI, CLI, or HTTP API.
>
> -- https://vaultproject.io

:::note
This is based on authentik 2022.2.1 and Vault 1.9.3. Instructions may differ between versions. This guide does not cover vault policies. See https://learn.hashicorp.com/tutorials/vault/oidc-auth?in=vault/auth-methods for a more in depth vault guide
:::

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of authentik installation.
- `vault.company` is the FQDN of Vault installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

### Step 1

In authentik, create an _OAuth2/OpenID Provider_ (under _Applications/Providers_) with these settings:

:::note
Only settings that have been modified from default have been listed.
:::

**Protocol Settings**

- Name: Vault
- Signing Key: Select any available key

- Redirect URIs/Origins:

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

- Name: Vault
- Slug: vault-slug
- Provider: Vault

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

## External Groups

If you wish to manage group membership in Hashicorp Vault via Authentik you have to use [external groups](https://developer.hashicorp.com/vault/tutorials/auth-methods/oidc-auth#create-an-external-vault-group).

:::note
This assumes that the steps above have already been completed and tested.
:::

### Step 1

In authentik, edit the OIDC provider created above. Under **Advanced protocol settings** add `authentik default OAuth Mapping: OpenID 'profile'` This includes the groups mapping.

### Step 2

In Vault, change the reader role to have the following settings:

```
vault write auth/oidc/role/reader \
      bound_audiences="Client ID" \
      allowed_redirect_uris="https://vault.company/ui/vault/auth/oidc/oidc/callback" \
      allowed_redirect_uris="https://vault.company/oidc/callback" \
      allowed_redirect_uris="http://localhost:8250/oidc/callback" \
      user_claim="sub" \
      policies="reader" \
      groups_claim="groups" \
      oidc_scopes=[ "openid profile email" ]
```

Add a group.

```
vault write identity/group/reader \
    name="reader" \
    policies=["reader"] \
    type="external"
```

Get the canonical ID of the group.

```
vault list identity/group/id
```

Get the ID of the OIDC accessor.

```
vault auth list
```

Add a group alias, this maps the group to the OIDC backend.

```
vault write identity/group-alias \
    mount_accessor="auth_oidc_xxxxxx" \
    canonical_id="group_id" \
    name="group name in authentik"
```

You should then be able to sign in via OIDC.
`vault login -method=oidc role="reader"`
