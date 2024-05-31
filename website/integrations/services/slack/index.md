---
title: Slack
---

<span class="badge badge--secondary">Support level: authentik</span>

## What is Slack

> Slack is a platform for collaboration, with chat and real-time video capabilities.
>
> -- https://slack.com

## Preparation

The following placeholders will be used:

-   `slack.company` is the FQDN of the Slack install.
-   `authentik.company` is the FQDN of the authentik install.

## authentik configuration

### Step 1. Create custom property mappings

Your Slack integration requires property mappings for `User.Email` and `User.Username` so that authetnik can retrieve and map these values from Slack.

1. Log in as admin to your authentik instance and then click **Admin interface**.
2. Navigate to **Customization -> Property Mappings** and then click **Create**.
3. On the **New property mapping** modal, select **SAML Property Mapping** and then click **Next**.
4. Define the required values. For **Expression** define `User.Email`, with `return request.user.email` and for `User.Username` use `return request.user.username`.
5. Click **Finish**.

### Step 2. Create a new authentication provider

1. Navigate to **Applications -> Providers** and then click **Create**.
2. On the **New provider** modal, select **SAML Provider** and then click **Next**.
3. Define the following values (values not listed below can be left as default or empty):
    - **Name**: provide a clear name, such as "Slack".
    - **Authorization flow**: Authorize Application (`default-provider-authorization-implicit-consent`).
    - **Protocol settings** define the following values:
        - **ACS URL**: `https:_workspace-name_.slack.com/sso/saml`
        - **Issuer**: `https://slack.com`.
        - **Service Provider Binding**: select **Post**
    - **Advanced protocol settings**
        - **Signing Certificate**: select the appproriate certificate for Slack.
    You can leave the default property mappings and other settings.
4. Click **Finish** to create the provider.

### Step 3. Create a new application

1. Navigate to **Applications -> Applications** and then click **Create**.
2. Provide a name for the new application.
3. Set the provider to the one you just created.
4. Ensure that the **Policy engine mode** is set to **ANY, any policy must match to grant access**.
5. Click **Create**.

## Slack configuration

### Step 4. Configure Slack

1. Log in to the Slack Admin Dashboard.
2. Navigate to the **Configure SAML Authetnication** page.
3. Enter the following values:
    - **SAML 2.0 Endpoint (HTTP)**: copy/paste in the **SSO URL (Redirect)** URL from authentik.
    - **Identity Provider Issuer**: set to https://slack.com
    - **Public Certificate**: add the certificate, which you can download from the authentik provider, under **Download signing certificate**.
4. Optionally, configure the other settings and customize the Sign in button label.
5. Click **Save**.
