---
title: Integrate with Hashicorp Vault
sidebar_label: Hashicorp Vault
support_level: authentik
---

## What is Vault

> Secure, store and tightly control access to tokens, passwords, certificates, encryption keys for protecting secrets and other sensitive data using a UI, CLI, or HTTP API.
>
> -- https://vaultproject.io

:::note
This is based on authentik 2022.2.1 and Vault 1.9.3. Instructions may differ between versions. This guide does not cover vault policies. See https://learn.hashicorp.com/tutorials/vault/oidc-auth?in=vault/auth-methods for a more in depth vault guide
:::

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.
- `vault.company` is the FQDN of the Vault installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Hashicorp Vault with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can create only an application, without a provider, by clicking **Create**.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Add three `Strict` redirect URIs and set them to <kbd>https://<em>vault.company</em>/ui/vault/auth/oidc/oidc/callback</kbd>, <kbd>https://<em>vault.company</em>/oidc/callback</kbd>, and <kbd>http://localhost:8250/oidc/callback</kbd>.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Hashicorp Vault configuration

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
