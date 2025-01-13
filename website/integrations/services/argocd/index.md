---
title: Integrate with ArgoCD
sidebar_label: ArgoCD
---

# ArgoCD

<span class="badge badge--secondary">Support level: Community</span>

## What is ArgoCD

> Argo CD is a declarative, GitOps continuous delivery tool for Kubernetes.
>
> -- https://argoproj.github.io/cd/

## Preparation

The following placeholders are used in this guide:

- `argocd.company` is the FQDN of the ArgoCD install.
- `authentik.company` is the FQDN of the authentik install.

:::note
Only settings that have been modified from default have been listed.
:::

## authentik Configuration

### Step 1 - Provider creation

In authentik, create an _OAuth2/OpenID Provider_ (under _Applications/Providers_) with these settings:

- Name: ArgoCD
- Client Type: `Confidential`
- Signing Key: Select any available key
- Redirect URIs:

```
https://argocd.company/api/dex/callback
http://localhost:8085/auth/callback
```

After creating the provider, take note of the `Client ID` and `Client Secret`, you'll need to give them to ArgoCD in the _ArgoCD Configuration_ field.

### Step 2 - Application creation

Create a new _Application_ (under _Applications/Applications_) with these settings:

- Name: ArgoCD
- Provider: ArgoCD
- Slug: argocd
- Launch URL: https://argocd.company/auth/login

### Step 3 - ArgoCD Group creation

Create a new _Group_ (under _Directory/Groups_) that'll be used as the admin group for ArgoCD (if you already have an "admin" group, you can skip this part!)

- Name: ArgoCD Admins
- Members: Add your user and/or any user that should be an ArgoCD admin

You can create another group for read-only access to ArgoCD as well if desired:

- Name: ArgoCD Viewers
- Members: Any user that should have ArgoCD read-only access

## Terraform provider

```hcl
data "authentik_flow" "default-provider-authorization-implicit-consent" {
  slug = "default-provider-authorization-implicit-consent"
}

data "authentik_flow" "default-provider-invalidation" {
  slug = "default-invalidation-flow"
}

data "authentik_property_mapping_provider_scope" "scope-email" {
  name = "authentik default OAuth Mapping: OpenID 'email'"
}

data "authentik_property_mapping_provider_scope" "scope-profile" {
  name = "authentik default OAuth Mapping: OpenID 'profile'"
}

data "authentik_property_mapping_provider_scope" "scope-openid" {
  name = "authentik default OAuth Mapping: OpenID 'openid'"
}

data "authentik_certificate_key_pair" "generated" {
  name = "authentik Self-signed Certificate"
}

resource "authentik_provider_oauth2" "argocd" {
  name          = "ArgoCD"
  #  Required. You can use the output of:
  #     $ openssl rand -hex 16
  client_id     = "my_client_id"

  # Optional: will be generated if not provided
  # client_secret = "my_client_secret"

  authorization_flow = data.authentik_flow.default-provider-authorization-implicit_consent.id
  invalidation_flow  = data.authentik_flow.default-provider-invalidation.id

  signing_key = data.authentik_certificate_key_pair.generated.id

  allowed_redirect_uris = [
    {
      matching_mode = "strict",
      url           = "https://argocd.company/api/dex/callback",
    },
    {
      matching_mode = "strict",
      url           = "http://localhost:8085/auth/callback",
    }
  ]

  property_mappings = [
    data.authentik_property_mapping_provider_scope.scope-email.id,
    data.authentik_property_mapping_provider_scope.scope-profile.id,
    data.authentik_property_mapping_provider_scope.scope-openid.id,
  ]
}

resource "authentik_application" "argocd" {
  name              = "ArgoCD"
  slug              = "argocd"
  protocol_provider = authentik_provider_oauth2.argocd.id
}

resource "authentik_group" "argocd_admins" {
  name    = "ArgoCD Admins"
}

resource "authentik_group" "argocd_viewers" {
  name    = "ArgoCD Viewers"
}
```

## ArgoCD Configuration

:::note
We're not going to use the oidc config, but instead the "dex", oidc doesn't allow ArgoCD CLI usage while DEX does.
:::

### Step 1 - Add the OIDC Secret to ArgoCD

In the `argocd-secret` Secret, add the following value to the `data` field:

```yaml
dex.authentik.clientSecret: <base 64 encoded value of the Client Secret from the Provider above>
```

If using Helm, the above can be added to `configs.secret.extra` in your ArgoCD Helm `values.yaml` file as shown below, securely substituting the string however you see fit:

```yaml
configs:
    secret:
        extra:
            dex.authentik.clientSecret: "${argocd_authentik_client_secret}"
```

### Step 2 - Configure ArgoCD to use authentik as OIDC backend

In the `argocd-cm` ConfigMap, add the following to the data field :

```yaml
url: https://argocd.company
dex.config: |
    connectors:
    - config:
        issuer: https://authentik.company/application/o/<application slug defined in step 2>/
        clientID: <client ID from the Provider above>
        clientSecret: $dex.authentik.clientSecret
        insecureEnableGroups: true
        scopes:
          - openid
          - profile
          - email
      name: authentik
      type: oidc
      id: authentik
```

### Step 3 - Map the `ArgoCD Admins` group to ArgoCD's admin role

In the `argocd-rbac-cm` ConfigMap, add the following to the data field (or create it if it's not already there) :

```yaml
policy.csv: |
    g, ArgoCD Admins, role:admin
    g, ArgoCD Viewers, role:readonly
```

If you already had an "admin" group and thus didn't create the `ArgoCD Admins` one, just replace `ArgoCD Admins` with your existing group name.
If you did not opt to create a read-only group, or chose to use one with a different name in authentik, rename or remove here accordingly.

Apply all the modified manifests, and you should be able to login to ArgoCD both through the UI and the CLI.
