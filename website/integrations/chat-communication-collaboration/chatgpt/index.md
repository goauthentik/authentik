---
title: Integrate with ChatGPT
sidebar_label: ChatGPT
support_level: community
---

## What is ChatGPT

> ChatGPT is OpenAI's conversational AI platform that provides chat-based assistance across the web and desktop applications.
> By connecting ChatGPT to authentik with OpenID Connect (OIDC), users in your verified ChatGPT domain will authenticate through authentik whenever they access ChatGPT.
>
> -- https://chatgpt.com/

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

:::note
ChatGPT only enables the **Manage SSO** wizard after you verify ownership of your domain in the ChatGPT admin console. Domain verification is outside the scope of this guide.
:::

## authentik configuration

To support the integration of ChatGPT with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (You can also create them separately and link them afterward.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID**, **Client Secret** and **slug** values because they will be required later.
        - Set a `Strict` **Redirect URI** to the value ChatGPT presents as the **Login redirect URI** during its SSO wizard. If you do not have this yet, return after completing Step&nbsp;2 of the ChatGPT configuration and add it.
        - Select any available signing certificate for the **Signing Key**.
        - Include the scopes `openid`, `email`, and `profile` so authentik releases the claims ChatGPT expects.
        - Under **Advanced protocol settings**, keep the default property mappings (`authentik default OAuth Mapping: OpenID Email` and `authentik default OAuth Mapping: OpenID Profile`). These mappings supply the `sub`, `email`, `given_name`, and `family_name` claims required by ChatGPT.
    - **Configure Bindings** _(optional)_: create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to control which users see the ChatGPT application on the **My Applications** page.
3. Click **Submit** to save the application and provider. If you deferred adding the ChatGPT redirect URI, edit the provider now and append it to the **Redirect URIs** list.

## ChatGPT configuration

1. Sign in to the ChatGPT admin console and go to `https://chatgpt.com/admin/identity`.
2. Under **Identity Management**, choose **Manage SSO**, then select **Custom OIDC** as the single sign-on method.
3. Complete the Custom OIDC wizard:
    1. **Provide an Identity Provider Name**: enter a descriptive name (for example, `authentik`).
    2. **Create an Application**: copy the **Login redirect URI** that ChatGPT displays and add it to the **Redirect URIs** field of your authentik OIDC provider if you have not done so already.
    3. **Add Claims**: confirm ChatGPT lists the required claims (`sub`, `email`, `given_name`, and `family_name`). These are provided by authentik’s default OIDC property mappings when the `email` and `profile` scopes are enabled.
    4. **Provide your OIDC Configuration**: paste the authentik **Client ID**, **Client Secret**, and the discovery endpoint `https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration`.
    5. **Configure Application Link**: review the direct sign-in link that ChatGPT generates; share it with users if needed.
    6. **Test Single Sign-On**: run the built-in test. ChatGPT should redirect you to authentik for authentication and report success.

## Configuration verification

1. Open a new browser session (or private window) and browse to `https://chatgpt.com`.
2. Select **Log in**, then enter an email address from the domain you verified in ChatGPT.
3. Confirm that the sign-in flow redirects to your authentik instance. Sign in with an account that is allowed to access the ChatGPT application.
4. After successfully authenticating in authentik, you should land back in ChatGPT with the conversation interface available. If ChatGPT reports an error, review the redirect URI, scopes, and client credentials configured in authentik.
