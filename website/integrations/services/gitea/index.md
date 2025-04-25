---
title: Integrate with Gitea
sidebar_label: Gitea
support_level: community
---

## What is Gitea

> Gitea is a community managed lightweight code hosting solution written in Go. It is published under the MIT license.
>
> -- https://gitea.io/

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
    - Set a `Strict` redirect URI to `https://gitea.company/user/oauth2/authentik/callback`.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Gitea configuration

1. Log in to Gitea as an admin, then click on your profile icon at the top right and select **Site Administration**.
2. Select the **Authentication Sources** tab and then click on **Add Authentication Source**.
3. Set the following required configurations:
    - **Authentication Name**: `authentik` (This must match the name used in the **Redirect URI** in the previous section)
    - **OAuth2 Provider**: `OpenID Connect`
    - **Client ID (Key)**: Enter the client ID from authentik.
    - **Client Secret**: Enter the Client Secret from authentik.
    - **Icon URL**: `https://authentik.company/static/dist/assets/icons/icon.png`
    - **OpenID Connect Auto Discovery URL**: `https://authentik.company/application/o/<slug>/.well-known/openid-configuration`
    - **Additional Scopes**: `email profile`

![](./gitea1.png)

4. Click **Add Authentication Source**.

### Claims for authorization management (optional)

:::note
This step is _optional_ and shows how to set claims to control the permissions of users in Gitea by adding them to groups.
:::

#### Create groups

The following groups will be created:

- `gituser`: normal Gitea users.
- `gitadmin`: Gitea users with administrative permissions.
- `gitrestricted`: restricted Gitea users.

:::note
Users who are in none of these groups will not be able to log in to gitea.
:::

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Directory** > **Groups** and click **Create**.
3. Set the name of the group as `gituser` and click **Create**.
4. Repeat steps 2 and 3 to create two additional groups named `gitadmin` and `gitrestricted`.
5. Click the name of a newly created group and navigate to the **Users** tab.
6. Click **Add existing user**, select the user/s that need Gitea access and click **Add**.
7. Repeat steps 5 and 6 for the two additional groups.

:::Note
Users can be added to the groups at any point
:::

#### Create custom property mapping

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**. Create a **Scope Mapping** with the following configurations:

    - **Name**: Choose a descriptive name (.e.g `authentik gitea OAuth Mapping: OpenID 'gitea'`)
    - **Scope name**: `gitea`
    - **Expression**:

    ```python showLineNumbers
    gitea_claims = {}

    if request.user.ak_groups.filter(name="gituser").exists():
        gitea_claims["gitea"]= "user"
    if request.user.ak_groups.filter(name="gitadmin").exists():
        gitea_claims["gitea"]= "admin"
    if request.user.ak_groups.filter(name="gitrestricted").exists():
        gitea_claims["gitea"]= "restricted"

    return gitea_claims
    ```

3. Click **Finish**.

#### Add the custom property mapping to the Gitea provider

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click on the **Edit** icon of the Gitea provider.
3. Under **Advanced protocol settings** > **Scopes** add the following scopes to **Selected Scopes**:

    - `authentik default OAuth Mapping: OpenID 'email'`
    - `authentik default OAuth Mapping: OpenID 'profile'`
    - `authentik default OAuth Mapping: OpenID 'openid'`
    - `authentik gitea OAuth Mapping: OpenID 'gitea'`

4. Click **Update**.

#### Configure Gitea to use the new claims

:::note
For this to function, the Gitea `ENABLE_AUTO_REGISTRATION: true` variable must be set. More information on configurations variables in the [Gitea Configuration Cheat Sheet](https://docs.gitea.com/administration/config-cheat-sheet).
:::

1. Log in to Gitea as an admin. Click on your profile icon at the top right > **Site Administration**.
2. Select the **Authentication Sources** tab and edit the **authentik** Authentication Source.
3. Set the following configurations:
    - **Additional Scopes**: `email profile gitea`
    - **Required Claim Name**: `gitea`
    - **Claim name providing group names for this source.** (Optional): `gitea`
    - **Group Claim value for administrator users.** (Optional - requires claim name to be set): `admin`
    - **Group Claim value for restricted users.** (Optional - requires claim name to be set): `restricted`
4. Click **Update Authentication Source**.

:::note
Users without any of the defined groups will no longer be able to log in.
Users of the group **gitadmin** will have administrative privileges, and users in the group **gitrestricted** will be restricted.
:::

### Helm Chart Configuration

authentik can be configured automatically in Kubernetes deployments using its [Helm chart](https://gitea.com/gitea/helm-chart/).

Add the following to your Gitea Helm chart `values.yaml` file:

```yaml showLineNumbers title="values.yaml"
gitea:
    oauth:
        - name: "authentik"
        provider: "openidConnect"
        key: "<CLIENT_ID_FROM_AUTHENTIK>" #Step 1
        secret: "<CLIENT_SECRET_FROM_AUTHENTIK>" #Step 1
        autoDiscoverUrl: "https://authentik.company/application/o/<slug>/.well-known/openid-configuration"
        iconUrl: "https://authentik.company/static/dist/assets/icons/icon.png"
        scopes: "email profile"
```

### Kubernetes Secret

Alternatively you can use a Kubernetes secret to set the `key` and `secret` values.

1. Create a Kubernetes secret with the following variables:

```yaml showLineNumbers
apiVersion: v1
kind: Secret
metadata:
    name: gitea-authentik-secret
type: Opaque
stringData:
    key: "<CLIENT_ID_FROM_AUTHENTIK>" #Step 1
    secret: "<Client secret from authentik>"
```

2. Add the following configurations to your Gitea Helm Chart `values.yaml` file:

```yaml showLineNumbers title="values.yaml"
gitea:
    oauth:
        - name: "authentik"
        provider: "openidConnect"
        existingSecret: gitea-authentik-secret
        autoDiscoverUrl: "https://authentik.company/application/o/<slug>/.well-known/openid-configuration"
        iconUrl: "https://authentik.company/static/dist/assets/icons/icon.png"
        scopes: "email profile"
```

## Configuration verification

To verify that authentik is correctly set up with Gitea, log out and then log back in using the **Sign in with authentik** button.
