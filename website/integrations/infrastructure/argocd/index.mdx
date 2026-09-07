---
title: Integrate with Argo CD
sidebar_label: Argo CD
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Argo CD?

> Argo CD is a declarative, GitOps continuous delivery tool for Kubernetes.
>
> -- https://argoproj.github.io/cd/

## Preparation

The following placeholders are used in this guide:

- `argocd.company` is the FQDN of the Argo CD installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Argo CD with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the application **Slug** because it will be required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://argocd.company/api/dex/callback`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

### Create the groups

Using the authentik Admin interface, navigate to **Directory** > **Groups** and click **Create** to create the groups that Argo CD will use for RBAC:

- `Argo CD Admins` for administrator users.
- `Argo CD Viewers` for read-only users.

After creating the groups, select a group, navigate to the **Users** tab, and manage its members by using the **Add existing user** and **Create user** buttons as needed.

## Argo CD configuration

This guide uses the bundled Dex connector in Argo CD. With this configuration, Argo CD can use authentik for the web UI and the CLI, and can map authentik groups to Argo CD RBAC roles.

### Add the client secret

In the `argocd-secret` Secret, add the following value to the `data` field:

```yaml title="argocd-secret"
dex.authentik.clientSecret: <base64_encoded_client_secret_from_authentik>
```

If you use the Argo CD Helm chart, add the client secret to `configs.secret.extra` instead:

```yaml title="values.yaml"
configs:
    secret:
        extra:
            dex.authentik.clientSecret: <Client Secret from authentik>
```

### Configure Dex

In the `argocd-cm` ConfigMap, add the following values to the `data` field:

```yaml title="argocd-cm"
url: https://argocd.company
dex.config: |
    connectors:
    - config:
        issuer: https://authentik.company/application/o/<application_slug>/
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

If you use the Argo CD Helm chart, add these values to `configs.cm` instead.

### Map the groups

In the `argocd-rbac-cm` ConfigMap, add the following values to the `data` field:

```yaml title="argocd-rbac-cm"
policy.csv: |
    g, Argo CD Admins, role:admin
    g, Argo CD Viewers, role:readonly
```

If you already use different group names in authentik, replace `Argo CD Admins` and `Argo CD Viewers` with the matching group names. If you do not need the read-only group, remove that line.

If you use the Argo CD Helm chart, add these values to `configs.rbac` instead.

Apply all modified manifests or Helm values. Group membership is evaluated when users authenticate, so users should log out and log back in after you change their Argo CD group membership.

## Configuration verification

To confirm that authentik is properly configured with Argo CD, open Argo CD and log in with authentik. You should also be able to log in with the Argo CD CLI.

## Resources

- [Argo CD documentation - User management and SSO](https://argo-cd.readthedocs.io/en/stable/operator-manual/user-management/)
- [Argo CD documentation - RBAC configuration](https://argo-cd.readthedocs.io/en/stable/operator-manual/rbac/)
- [Argo CD Helm chart values](https://github.com/argoproj/argo-helm/blob/main/charts/argo-cd/values.yaml)
- [Dex documentation - OpenID Connect connector](https://dexidp.io/docs/connectors/oidc/)
