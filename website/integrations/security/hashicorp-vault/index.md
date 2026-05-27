---
title: Integrate with HashiCorp Vault
sidebar_label: HashiCorp Vault
support_level: authentik
---

## What is HashiCorp Vault?

> HashiCorp Vault secures, stores, and controls access to tokens, passwords, certificates, encryption keys, and other sensitive data.
>
> -- https://developer.hashicorp.com/vault

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.
- `vault.company` is the FQDN of the HashiCorp Vault installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of HashiCorp Vault with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
        - Set two `Strict` redirect URIs to `https://vault.company/ui/vault/auth/oidc/oidc/callback` and `http://localhost:8250/oidc/callback`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

## HashiCorp Vault configuration

This guide assumes that the Vault OIDC auth method is mounted at `oidc`, which is the path used by `vault auth enable oidc`. If you mount the auth method at a different path, replace `oidc` in the Vault paths and in the Vault UI redirect URI.

:::info[Vault policies]
This guide configures OIDC authentication only. Create the Vault policies that you reference, such as `reader`, according to your Vault access model before assigning them to roles or identity groups.
:::

1. Enable the OIDC auth method.

    ```bash
    vault auth enable oidc
    ```

2. Configure the OIDC auth method with the authentik provider details.

    ```bash
    vault write auth/oidc/config \
        oidc_discovery_url="https://authentik.company/application/o/<application_slug>/" \
        oidc_client_id="<Client ID from authentik>" \
        oidc_client_secret="<Client secret from authentik>" \
        default_role="reader"
    ```

3. Create a Vault OIDC role named `reader`.

    ```bash
    vault write auth/oidc/role/reader \
        bound_audiences="<Client ID from authentik>" \
        allowed_redirect_uris="https://vault.company/ui/vault/auth/oidc/oidc/callback" \
        allowed_redirect_uris="http://localhost:8250/oidc/callback" \
        user_claim="sub" \
        token_policies="reader"
    ```

## External groups

You can optionally use Vault external identity groups to assign Vault policies based on authentik group membership.

This example maps an authentik group named `vault-reader` to a Vault external group that grants the `reader` policy. The authentik default `profile` scope mapping supplies the `groups` claim used by Vault.

1. Update the `reader` role to request the `profile` scope and read group membership from the `groups` claim.

    ```bash
    vault write auth/oidc/role/reader \
        bound_audiences="<Client ID from authentik>" \
        allowed_redirect_uris="https://vault.company/ui/vault/auth/oidc/oidc/callback" \
        allowed_redirect_uris="http://localhost:8250/oidc/callback" \
        user_claim="sub" \
        groups_claim="groups" \
        oidc_scopes="profile"
    ```

2. Create an external Vault group for the `vault-reader` authentik group.

    ```bash
    vault write identity/group/name/vault-reader \
        policies="reader" \
        type="external"

    VAULT_GROUP_ID=$(vault read -field=id identity/group/name/vault-reader)
    ```

3. Get the OIDC auth method mount accessor.

    ```bash
    OIDC_ACCESSOR=$(vault read -field=accessor sys/auth/oidc)
    ```

4. Create a group alias that maps the authentik group name to the Vault group.

    ```bash
    vault write identity/group-alias \
        name="vault-reader" \
        mount_accessor="$OIDC_ACCESSOR" \
        canonical_id="$VAULT_GROUP_ID"
    ```

## Configuration verification

To confirm that authentik is properly configured with HashiCorp Vault, open Vault and select **OIDC** from the authentication method list. Sign in through the OIDC flow and confirm that Vault redirects you to authentik for authentication and then back to Vault.

You can also verify the CLI flow with the following command:

```bash
vault login -method=oidc role="reader"
```

## Resources

- [HashiCorp Developer - Vault](https://developer.hashicorp.com/vault)
- [HashiCorp Developer - Use JWT/OIDC authentication](https://developer.hashicorp.com/vault/docs/auth/jwt)
- [HashiCorp Developer - JWT/OIDC auth method API](https://developer.hashicorp.com/vault/api-docs/auth/jwt)
- [HashiCorp Developer - Identity group API](https://developer.hashicorp.com/vault/api-docs/secret/identity/group)
- [HashiCorp Developer - Identity group alias API](https://developer.hashicorp.com/vault/api-docs/secret/identity/group-alias)
