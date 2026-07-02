---
title: Integrate with Gitea
sidebar_label: Gitea
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Gitea?

> Gitea is a community managed lightweight code hosting solution written in Go. It is published under the MIT license.
>
> -- https://gitea.io/

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.
- `gitea.company` is the FQDN of the Gitea installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Gitea with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the application **Slug** because it will be required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://gitea.company/user/oauth2/authentik/callback`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

### Configure authorization claims _(optional)_

You can use application entitlements and a custom property mapping to let Gitea assign administrator permissions, restricted-user status, and organization team membership from authentik.

Create the authorization claim only if Gitea should manage those permissions from authentik. Users who do not receive any of the entitlements in this section will be denied access after you configure Gitea to require the claim.

#### Create entitlements

Create the following application entitlements:

- `gituser`: normal Gitea users.
- `gitadmin`: Gitea users with administrative permissions.
- `gitrestricted`: restricted Gitea users.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and open the Gitea application.
3. Click the **Application entitlements** tab.
4. Click **Create entitlement**, set the name to `gituser`, and then click **Create**.
5. Repeat step 4 to create two additional entitlements named `gitadmin` and `gitrestricted`.
6. Open an entitlement and bind the users or groups that need Gitea access to it.
7. Repeat step 6 for the two additional entitlements.

#### Create custom property mapping

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**. Create a **Scope Mapping** with the following configurations:
    - **Name**: Choose a descriptive name (e.g. `authentik gitea OAuth Mapping: OpenID 'gitea'`)
    - **Scope name**: `gitea`
    - **Expression**:

    ```python showLineNumbers
    entitlement_names = {
        entitlement.name
        for entitlement in request.user.app_entitlements(provider.application)
    }
    gitea_claims = {}

    groups = []

    if "gituser" in entitlement_names:
        groups.append("user")
    if "gitadmin" in entitlement_names:
        groups.append("admin")
    if "gitrestricted" in entitlement_names:
        groups.append("restricted")

    if groups:
        gitea_claims["gitea"] = groups

    return gitea_claims
    ```

3. Click **Finish**.

#### Add the mapping to the provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click the **Edit** icon of the Gitea provider.
3. Under **Advanced protocol settings** > **Scopes**, add `authentik gitea OAuth Mapping: OpenID 'gitea'` to **Selected Scopes**.
4. Click **Update**.

## Gitea configuration

1. Log in to Gitea as an administrator, then click your profile icon in the top-right corner and select **Site Administration**.
2. Select the **Authentication Sources** tab and then click **Add Authentication Source**.
3. Set the following required configurations:
    - **Authentication Name**: `authentik`. This value is part of the callback URL, so it must match the value used in the authentik **Redirect URI**.
    - **OAuth2 Provider**: `OpenID Connect`
    - **Client ID (Key)**: enter the **Client ID** from authentik.
    - **Client Secret**: enter the **Client Secret** from authentik.
    - **Icon URL**: `https://authentik.company/static/dist/assets/icons/icon.png`
    - **OpenID Connect Auto Discovery URL**: `https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration`
    - **Additional Scopes**: `email profile`

4. Click **Add Authentication Source**.

### Evaluate authorization claims _(optional)_

If you created the authorization claim in authentik, configure Gitea to request and evaluate it.

1. In Gitea, return to **Site Administration** > **Authentication Sources** and edit the **authentik** authentication source.
2. Set **Additional Scopes** to `email profile gitea`.
3. Set **Required Claim Name** to `gitea`.
4. To use the same claim for Gitea permissions and team membership, set the following values:
    - **Claim name providing group names for this source.**: `gitea`
    - **Group Claim value for administrator users.**: `admin`
    - **Group Claim value for restricted users.**: `restricted`
    - **Map claimed groups to Organization teams.**: `{"admin":{"Acme":["Owners"]}}`
5. Click **Update Authentication Source**.

The organization team mapping example adds users with the `gitadmin` entitlement to the `Owners` team in the `Acme` organization. Replace `Acme` and `Owners` with the Gitea organization and team names that should receive synchronized users. The organization and team must already exist in Gitea.

### Configure the Helm chart _(optional)_

authentik authentication can be configured automatically in Kubernetes deployments using the Gitea Helm chart.

Add the following to your Gitea Helm chart `values.yaml` file:

```yaml showLineNumbers title="values.yaml"
gitea:
    oauth:
        - name: "authentik"
        provider: "openidConnect"
        key: "<Client ID from authentik>"
        secret: "<Client Secret from authentik>"
        autoDiscoverUrl: "https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration"
        iconUrl: "https://authentik.company/static/dist/assets/icons/icon.png"
        scopes: "email profile"
```

### Use a Kubernetes secret _(optional)_

You can use a Kubernetes secret to store and manage the sensitive `key` and `secret` values.

1. Create a Kubernetes secret with the following variables:

```yaml showLineNumbers
apiVersion: v1
kind: Secret
metadata:
    name: gitea-authentik-secret
type: Opaque
stringData:
    key: "<Client ID from authentik>"
    secret: "<Client Secret from authentik>"
```

2. Add the following configurations to your Gitea Helm chart `values.yaml` file:

```yaml showLineNumbers title="values.yaml"
gitea:
    oauth:
        - name: "authentik"
        provider: "openidConnect"
        existingSecret: gitea-authentik-secret
        autoDiscoverUrl: "https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration"
        iconUrl: "https://authentik.company/static/dist/assets/icons/icon.png"
        scopes: "email profile"
```

## Configuration verification

To confirm that authentik is properly configured with Gitea, log out of Gitea and open the Gitea integration from authentik. On the Gitea login page, click **Sign in with authentik**.

## Resources

- [Gitea Docs - Configuration cheat sheet](https://docs.gitea.com/administration/config-cheat-sheet)
- [Gitea Docs - Command line admin authentication sources](https://docs.gitea.com/administration/command-line#admin)
- [Gitea Helm chart - OAuth2 settings](https://gitea.com/gitea/helm-gitea/src/branch/main/README.md#oauth2-settings)
