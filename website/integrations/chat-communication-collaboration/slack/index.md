---
title: Integrate with Slack
sidebar_label: Slack
support_level: authentik
---

## What is Slack

> Slack is a platform for collaboration, with chat and real-time video capabilities. To learn more, visit https://slack.com.

## Preparation

The following placeholders are used in this guide:

- `company.slack.com` is the FQDN of your Slack workspace.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

For additional information about integrating with Slack, refer to their [documentation](https://slack.com/help/docs/205168057-Custom-SAML-single-sign-on).

## SAML Login Integration

### authentik configuration

To support the integration of Slack with authentik, you need to create an application/provider pair in authentik.

#### Create property mappings

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**. Create two **SAML Provider Property Mapping**s with the following settings:
    - **Name Mapping:**
        - **Name**: Choose a descriptive name
        - **SAML Attribute Name**: `User.Email`
        - **Friendly Name**: Leave blank
        - **Expression**: `return request.user.email`
    - **Email Mapping:**
        - **Name**: Choose a descriptive name
        - **SAML Attribute Name**: `User.Username`
        - **Friendly Name**: Leave blank
        - **Expression**: `return request.user.username`

#### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **slug** as it will be required later.
- **Choose a Provider type**: select **SAML Provider** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Set the **ACS URL** to `https://company.slack.com/sso/saml`.
    - Set the **Issuer** to `https://slack.com`.
    - Set the **Service Provider Binding** to `Post`.
    - Under **Advanced protocol settings**, select an available **Signing certificate** and add the two **Property Mappings** you created in the previous section.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

### Slack configuration

#### Configure Slack

1. Log in to the Slack Admin Dashboard.
2. Navigate to the **Configure SAML Authentication** page.
3. Enter the following values:
    - **SAML 2.0 Endpoint (HTTP)**: copy/paste in the **SSO URL (Redirect)** URL from the provider that you created in authentik. **Example**: `https://_authentik.company_/applications/saml/slack/sso/binding/redirect/`
    - **Identity Provider Issuer**: set to `https://slack.com`
    - **Public Certificate**: add the certificate, which you can download from the authentik provider, under **Download signing certificate**.
4. Optionally, configure the other settings and customize the Sign in button label.
5. Click **Save**.

## SCIM Integration

You can configure SCIM with Slack, allowing you to automatically make new slack users once your authentik database is updated with a new user.

### Configure Slack

SCIM requires having a Slack account that is Business+ level or higher.

#### Create a Slack application on your workspace

1. Navigate to the [Slack App creation page](https://api.slack.com/apps?new_app=1) and create a new application.
2. After creating the application, click **OAuth & Permissions** in the sidebar.
3. Under **User Token Scopes**, add the `admin` scope.
4. Refresh the page.
5. Click **Install to Workspace** to add the application to your workspace.
6. Copy the generated **User OAuth Token**.

### Configure authentik

#### Create a SCIM provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click **Create**.
3. Select **SCIM Provider** as the provider type and click **Next**.
4. Enter the following values:
    - **Name**: Choose a descriptive name.
    - **URL**: `https://api.slack.com/scim/v2/`
    - **Token**: Paste the admin token you copied from Slack.
    - **Compatibility Mode**: Select **Slack**.
5. Click **Finish** to save the provider.

#### Add the SCIM provider to your application

1. Navigate to **Applications** > **Applications** and select your Slack application.
2. Click **Edit**.
3. In the **Backchannel Providers** field, select the SCIM provider you created.
4. Click **Update** to save the application.
