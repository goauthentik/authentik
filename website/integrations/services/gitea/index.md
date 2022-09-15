---
title: Gitea
---

<span class="badge badge--secondary">Support level: Community</span>

## What is Gitea

From https://gitea.io/

:::note
Gitea is a community managed lightweight code hosting solution written in Go. It is published under the MIT license.
:::

:::note
This is based on authentik 2021.10.3 and Gitea 1.16.0+rc1 installed using https://docs.gitea.io/en-us/install-from-binary/. Instructions may differ between versions.
:::

## Preparation

The following placeholders will be used:

-   `authentik.company` is the FQDN of authentik.
-   `gitea.company` is the FQDN of Gitea.

### Step 1

In authentik, create an _OAuth2/OpenID Provider_ (under _Resources/Providers_) with these settings:

:::note
Only settings that have been modified from default have been listed.
:::

**Protocol Settings**

-   Name: Gitea
-   Signing Key: Select any available key

:::note
Take note of the `Client ID` and `Client Secret`, you'll need to give them to Gitea in _Step 3_.
:::

### Step 2

In authentik, create an application (under _Resources/Applications_) which uses this provider. Optionally apply access restrictions to the application using policy bindings.

:::note
Only settings that have been modified from default have been listed.
:::

-   Name: Gitea
-   Slug: gitea-slug
-   Provider: Gitea

### Step 3

Navigate to the _Authentication Sources_ page at https://gitea.company/admin/auths and click `Add Authentication Source`

Change the following fields

-   Authentication Name: authentik
-   OAuth2 Provider: OpenID Connect
-   Client ID (Key): Step 1
-   Client Secret: Step 1
-   Icon URL: https://goauthentik.io/img/icon.png
-   OpenID Connect Auto Discovery URL: https://authentik.company/application/o/gitea-slug/.well-known/openid-configuration
-   Additional Scopes: `email profile`

![](./gitea1.png)

`Add Authentication Source` and you should be done. Your Gitea login page should now have a `Sign in With` followed by the authentik logo which you can click on to sign-in to Gitea with Authentik creds.

## Helm Chart Configuration

authentik can be configured automatically in Gitea Kubernetes deployments via it's [Helm Chart](https://gitea.com/gitea/helm-chart/).

:::note
This is based on authentik 2022.8.2, Gitea v17.2, and Gitea Helm Chart v6.0.1. Instructions may differ between versions.
:::

Add the following to the Gitea Helm Chart `values.yaml` file:

```yaml
gitea:
    oauth:
        - name: "authentik"
          provider: "openidConnect"
          key: "CLIENT_ID_FROM_AUTHENTIK" #Step 1
          secret: "CLIENT_SECRET_FROM_AUTHENTIK" #Step 1
          autoDiscoveryUrl: "https://authentik.company/application/o/gitea-slug/.well-known/openid-configuration"
          iconUrl: "https://goauthentik.io/img/icon.png"
          scopes: "email profile"
```

### Kubernetes Secret

Alternatively you can use a Kubernetes secret to set the `key` and `secret` values.

Create a Kubernetes secret with the following:

```yaml
apiVersion: v1
kind: Secret
metadata:
    name: gitea-authentik-secret
type: Opaque
stringData:
    key: "CLIENT_ID_FROM_AUTHENTIK" #Step 1
    secret: "CLIENT_SECRET_FROM_AUTHENTIK" #Step 1
```

Add the following to the Gitea Helm Chart `values.yaml` file:

```yaml
gitea:
    oauth:
        - name: "authentik"
          provider: "openidConnect"
          existingSecret: gitea-authentik-secret
          autoDiscoveryUrl: "https://authentik.company/application/o/gitea-slug/.well-known/openid-configuration"
          iconUrl: "https://goauthentik.io/img/icon.png"
          scopes: "email profile"
```
