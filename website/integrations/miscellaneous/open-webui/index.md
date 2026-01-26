---
title: Integrate with Open WebUI
sidebar_label: Open WebUI
support_level: community
---

## What is Open WebUI

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

To support the integration of Open WebUI with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to `https://openwebui.company/oauth/oidc/callback`.
    - Select any available signing key.
    - Make sure to leave the **Encryption Key** field empty.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Open WebUI configuration

To configure authentik with Open WebUI, you must add the following environment variables to your OpenWebUI deployment:

:::warning
`WEBUI_URL` is a persistent configuration setting and must be set before enabling SSO. Changing it later requires either disabling persistent configuration or updating it in the Admin panel. More information can be found in the [Open WebUI documentation](https://docs.openwebui.com/getting-started/env-configuration/#important-note-on-persistentconfig-environment-variables).
:::

```yaml
OAUTH_CLIENT_ID=<client_id>
OAUTH_CLIENT_SECRET=<client_secret>
OAUTH_PROVIDER_NAME=authentik
OPENID_PROVIDER_URL=https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration
OPENID_REDIRECT_URI=https://openwebui.company/oauth/oidc/callback
WEBUI_URL=https://openwebui.company
# Allows auto-creation of new users using OAuth. Must be paired with ENABLE_LOGIN_FORM=false.
ENABLE_OAUTH_SIGNUP=true
# Disables user/password login form. Required when ENABLE_OAUTH_SIGNUP=true.
ENABLE_LOGIN_FORM=false
OAUTH_MERGE_ACCOUNTS_BY_EMAIL=true
```

Then restart Open WebUI to apply the changes.

## Configuration verification

- Open your web browser and go to `https://openwebui.company`.
- Make sure you are logged off any previous session.
- Click **Continue with authentik** to log in.
- After logging in, authentik will redirect you back to `https://openwebui.company`.
- If you successfully return to the Open WebUI, the login is working correctly.

:::info
Users are automatically created, but an administrator must update their role to at least **User** via the WebGUI.
To do so, log in as an administrator and access the **Admin Panel** (URL: `https://openwebui.company`/admin/users).
Click on the user whose role should be increased from **Pending** to at least **User**.
More details on how to administer Open WebUI can be found here `https://docs.openwebui.com/`.
:::

## References

- [Open WebUI Documentation - Federated Authentication Support](https://docs.openwebui.com/features/sso/)
