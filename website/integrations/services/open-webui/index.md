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

:::note
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
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to `https://openwebui.company/oauth/oidc/callback`.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Open WebUI configuration

You need to set the environment variables in the appropriate place based on your deployment method—either in the .env file or as Docker environment variables. The values themselves remain the same, only their location differs.

Enter the following details from the authentik provider:

- Set **OAUTH_CLIENT_ID** to the Client ID copied from authentik.
- Set **OAUTH_CLIENT_SECRET** to the Client Secret copied from authentik.
- Set **OAUTH_PROVIDER_NAME** to `authentik`.
- Set **OPENID_PROVIDER_URL** to `https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration`.
- Set **OPENID_REDIRECT_URI** to `https://openwebui.company/oauth/oidc/callback`.
- If you wish for new users to be created on Open Web UI, set **ENABLE_OAUTH_SIGNUP** to 'true'.

## Configuration verification

- Open your web browser and go to `https://openwebui.company`.
- Make sure you are logged off any previous session.
- Click **Continue with authentik** to log in.
- After logging in, authentik will redirect you back to `https://openwebui.company`.
- If you successfully return to the Open WebUI, the login is working correctly.

:::note
Users are automatically created, but an administrator must update their role to at least **User** via the WebGUI.
To do so, log in as an administrator and access the **Admin Panel** (URL: `https://openwebui.company`/admin/users).
Click on the user whose role should be increased from **Pending** to at least **User**.
More details on how to administer Open WebUI can be found here `https://docs.openwebui.com/`.
:::
