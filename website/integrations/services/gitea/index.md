---
title: Integrate with Gitea
sidebar_label: Gitea
support_level: community
---

## What is Gitea

> Gitea is a community managed lightweight code hosting solution written in Go. It is published under the MIT license.
>
> -- https://gitea.io/

:::note
This is based on authentik 2022.10.1 and Gitea 1.17.3 installed using the official docker image [https://docs.gitea.io/en-us/install-with-docker/](https://docs.gitea.io/en-us/install-with-docker/). Instructions may differ between versions.
:::

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.
- `gitea.company` is the FQDN of the Gitea installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Gitea with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to <kbd>https://<em>gitea.company</em>/user/oauth2/authentik/callback</kbd>.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

### Step 3

Navigate to the _Authentication Sources_ page at https://gitea.company/admin/auths and click `Add Authentication Source`

Change the following fields

- Authentication Name: authentik
- OAuth2 Provider: OpenID Connect
- Client ID (Key): Step 1
- Client Secret: Step 1
- Icon URL: https://authentik.company/static/dist/assets/icons/icon.svg
- OpenID Connect Auto Discovery URL: https://authentik.company/application/o/gitea-slug/.well-known/openid-configuration
- Additional Scopes: `email profile`

![](./gitea1.png)

`Add Authentication Source` and you should be done. Your Gitea login page should now have a `Sign in With` followed by the authentik logo which you can click on to sign-in to Gitea with Authentik creds.

### Step 4 _(optional Claims for authorization management)_

:::note
This step is **optional** and shows how to set claims to control the permissions of users in gitea by adding them to groups.
:::

#### Define Groups

The following groups will be used:

- `gituser` for normal Gitea users.
- `gitadmin` for Gitea users with administrative permissions.
- `gitrestricted` for restricted Gitea users.

:::note
Users who are in none of these groups will not be able to log in to gitea.
:::

In authentik, create three groups (under _Directory/Groups_) with the _Name_ as mentioned above and leave other settings untouched.

:::note
You can add Members to the groups now or anytime later.
:::

#### Create Custom Property Mapping

In authentik, create a custom property mapping (under _Customization/Property Mappings_) which has the type **Scope Mapping**.

:::note
Only settings that have been modified from default have been listed.
:::

- Name: authentik gitea OAuth Mapping: OpenID 'gitea'
- Scope name: gitea

And as **Expression** set the following:

```(python)
gitea_claims = {}
if request.user.ak_groups.filter(name="gituser").exists():
    gitea_claims["gitea"]= "user"
if request.user.ak_groups.filter(name="gitadmin").exists():
    gitea_claims["gitea"]= "admin"
if request.user.ak_groups.filter(name="gitrestricted").exists():
    gitea_claims["gitea"]= "restricted"

return gitea_claims
```

#### Add the custom Property Mapping to the Gitea Provider

In authentik, edit the **Gitea** provider (under _Applications/Providers_) by clicking the pencil Icon.

Unfold the _Advanced protocol settings_ and activate these Mappings:

- authentik default OAuth Mapping: OpenID 'email'
- authentik default OAuth Mapping: OpenID 'profile'
- authentik default OAuth Mapping: OpenID 'openid'
- authentik gitea OAuth Mapping: OpenID 'gitea'

Click `Update` and the configuration authentik is done.

#### Configure Gitea to use the new claims

:::note
Gitea must set `ENABLE_AUTO_REGISTRATION: true`.
:::

Navigate to the _Authentication Sources_ page at https://gitea.company/admin/auths and edit the **authentik** Authentication Source.

Change the following fields

- Additional Scopes: `email profile gitea`
- Required Claim Name: `gitea`
- Claim name providing group names for this source. (Optional): `gitea`
- Group Claim value for administrator users. (Optional - requires claim name above): `admin`
- Group Claim value for restricted users. (Optional - requires claim name above): `restricted`

`Update Authentication Source` and you should be done.

Users without any of the defined groups should no longer be able to log in.
Users of the group **gitadmin** should have administrative privileges, and users in the group **gitrestricted** should be restricted.

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
          autoDiscoverUrl: "https://authentik.company/application/o/gitea-slug/.well-known/openid-configuration"
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
          autoDiscoverUrl: "https://authentik.company/application/o/gitea-slug/.well-known/openid-configuration"
          iconUrl: "https://goauthentik.io/img/icon.png"
          scopes: "email profile"
```
