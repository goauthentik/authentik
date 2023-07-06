---
title: ArgoCD
---

<span class="badge badge--secondary">Support level: Community</span>

## What is ArgoCD

From https://argoproj.github.io/cd/

:::note
Argo CD is a declarative, GitOps continuous delivery tool for Kubernetes.
:::

## Preparation

The following placeholders will be used:

-   `argocd.company` is the FQDN of the ArgoCD install.
-   `authentik.company` is the FQDN of the authentik install.

:::note
Only settings that have been modified from default have been listed.
:::

## authentik Configuration

### Step 1 - Provider creation

In authentik, create an _OAuth2/OpenID Provider_ (under _Applications/Providers_) with these settings:

-   Name: ArgoCD
-   Client Type: `Confidential`
-   Signing Key: Select any available key
-   Redirect URIs:

```
http://argocd.company/api/dex/callback
http://localhost:8085/auth/callback
```

After creating the provider, take note of the `Client ID` and `Client Secret`, you'll need to give them to ArgoCD in the _ArgoCD Configuration_ field.

### Step 2 - Application creation

Create a new _Application_ (under _Applications/Applications_) with these settings:

-   Name: ArgoCD
-   Provider: ArgoCD
-   Slug: argocd
-   Launch URL: http://argocd.company/auth/login

### Step 3 - ArgoCD Admin Group creation

Create a new _Group_ (under _Directory/Groups_) that'll be used as the admin group for ArgoCD (if you already have an "admin" group, you can skip this part!)

-   Name: ArgoCD Admins
-   Members: Add your user and/or any user that should be an ArgoCD admin

## ArgoCD Configuration

:::note
We're not going to use the oidc config, but instead the "dex", oidc doesn't allow ArgoCD CLI usage while DEX does.
:::

### Step 1 - Add the OIDC Secret to ArgoCD

In the `argocd-secret` Secret, add the following value to the `data` field:

```yaml
dex.authentik.clientSecret: <base 64 encoded value of the Client Secret from the Provider above>
```

### Step 2 - Configure ArgoCD to use authentik as OIDC backend

In the `argocd-cm` ConfigMap, add the following to the data field :

```yaml
dex.config: |
    connectors:
    - config:
        issuer: http://authentik.company/application/o/<application slug defined in step 2>/
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
```

If you already had an "admin" group and thus didn't create the `ArgoCD Admins` one, just replace `ArgoCD Admins` with your existing group name.

Apply all the modified manifests, and you should be able to login to ArgoCD both through the UI and the CLI.
