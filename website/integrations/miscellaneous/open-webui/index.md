---
title: Integrate with Open WebUI
sidebar_label: Open WebUI
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Open WebUI?

> Open WebUI is a simple, self-hosted AI platform that works entirely offline. It supports tools like Ollama and OpenAI-style APIs and has a built-in engine for RAG tasks.
>
> -- https://openwebui.com/

## Preparation

The following placeholders are used in this guide:

- `openwebui.company` is the FQDN of the Open WebUI installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Open WebUI with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the application **Slug** value because it will be required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://openwebui.company/oauth/oidc/callback`.
        - Select any available signing key.
        - Make sure to leave the **Encryption Key** field empty.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

### Configure application roles _(optional)_

Open WebUI can assign the `user` and `admin` roles from OAuth claims. To manage these roles in authentik, create application entitlements and send them in a `roles` claim.

1. In authentik, navigate to **Applications** > **Applications** and open the Open WebUI application.
2. Click the **Application entitlements** tab.
3. Click **New Entitlement**, set the name to `Open WebUI Users`, and then click **Create**.
4. Repeat the previous step to create another entitlement named `Open WebUI Admins`.
5. Open each entitlement and bind the users or groups that should receive it.
6. Navigate to **Customization** > **Property Mappings** and click **Create**. Create a **Scope Mapping** with the following values:
    - **Name**: `Open WebUI roles`
    - **Scope name**: `roles`
    - **Expression**:

    ```python showLineNumbers
    entitlement_names = {
        entitlement.name
        for entitlement in request.user.app_entitlements(provider.application)
    }
    roles = []

    if "Open WebUI Users" in entitlement_names:
        roles.append("user")

    if "Open WebUI Admins" in entitlement_names:
        roles.append("admin")

    return {
        "roles": roles,
    }
    ```

7. Click **Finish**.
8. Navigate to **Applications** > **Providers**, edit the Open WebUI provider, and add `Open WebUI roles` to **Advanced protocol settings** > **Selected Scopes**.
9. Click **Update** to save the provider.

## Open WebUI configuration

To configure Open WebUI to use authentik, add the following environment variables to your Open WebUI deployment:

:::warning Persistent Open WebUI configuration
Open WebUI persists several configuration values, including `WEBUI_URL` and the OAuth settings. Set these values before enabling SSO, or update them later in the Open WebUI Admin Panel.
:::

```env title=".env"
OAUTH_CLIENT_ID="<Client ID from authentik>"
OAUTH_CLIENT_SECRET="<Client Secret from authentik>"
OAUTH_PROVIDER_NAME="authentik"
OPENID_PROVIDER_URL="https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration"
OPENID_REDIRECT_URI="https://openwebui.company/oauth/oidc/callback"
WEBUI_URL="https://openwebui.company"
ENABLE_OAUTH_SIGNUP="true"
ENABLE_LOGIN_FORM="false"
ENABLE_PASSWORD_AUTH="false"
OAUTH_MERGE_ACCOUNTS_BY_EMAIL="true"
```

Replace `<application_slug>` with the authentik application **Slug** noted earlier. Then restart Open WebUI to apply the changes.

To manage Open WebUI roles with the optional authentik application entitlements created earlier, add the following variables:

```env title=".env"
OAUTH_SCOPES="openid email profile roles"
ENABLE_OAUTH_ROLE_MANAGEMENT="true"
```

## Configuration verification

To confirm that authentik is properly configured with Open WebUI, open Open WebUI, make sure you are logged out of any previous session, and click **Continue with authentik**. After successful authentication, authentik redirects you back to Open WebUI.

If you enabled role management, assign a test user to one of the Open WebUI application entitlements in authentik, then log in as that user. To verify the assigned role, log in as an Open WebUI administrator, click your profile picture, select **Admin Panel**, and open the **Users** page.

## Resources

- [Open WebUI Documentation - SSO (OAuth, OIDC, Trusted Header)](https://docs.openwebui.com/features/authentication-access/auth/sso/)
- [Open WebUI Documentation - Environment Variable Configuration](https://docs.openwebui.com/reference/env-configuration/)
