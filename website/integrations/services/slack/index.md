---
title: Integrate with Slack
sidebar_label: Slack
---

# Slack

<span class="badge badge--primary">Support level: authentik</span>

## What is Slack

> Slack is a platform for collaboration, with chat and real-time video capabilities. To learn more, visit https://slack.com.

## Preparation

The following placeholder will be used:

- You can use <kbd>slack.<em>company</em>></kbd> or <kbd><em>my-workspace</em>.slack.com</kbd> as the FQDN of your Slack instance.
- You can use <kbd>authentik.company</kbd> as the FQDN of the authentik installation.

For additional information about integrating with Slack, refer to their [documentation](https://slack.com/help/articles/205168057-Custom-SAML-single-sign-on).

## authentik configuration

### Step 1. Create custom property mappings

Your Slack integration requires two property mappings, one each for `User.Email` and `User.Username`, so that authentik can retrieve and map these values from Slack.

1. Log in as admin to your authentik instance and then click **Admin interface**.
2. Navigate to **Customization -> Property Mappings**.
3. Create the property mapping for `User.Email`.
    1. On the **Property Mappings** page, click **Create**.
    2. On the **New property mapping** modal, select **SAML Property Mapping** and then click **Next**.
    3. Define the required values. In the **Expression** field, define `User.Email` as `return request.user.email`.
4. Click **Finish**.
5. Create the property mapping for `User.Username`.
    1. On the **Property Mappings** page, click **Create**.
    2. On the **New property mapping** modal, select **SAML Property Mapping** and then click **Next**.
    3. Define the required values. In the **Expression** field, define `User.Username` as `return request.user.username`.
6. Click **Finish**.

### Step 2. Create a new authentication provider

1. Navigate to **Applications -> Providers** and then click **Create**.
2. On the **New provider** modal, select **SAML Provider** and then click **Next**.
3. Define the following values (values not listed below can be left as default or empty):
    - **Name**: provide a clear name, such as "slack".
    - **Authorization flow**: Authorize Application (`default-provider-authorization-implicit-consent`).
    - **Protocol settings** define the following values:
        - **ACS URL**: `https://_workspace-name_.slack.com/sso/saml`
        - **Issuer**: `https://slack.com`.
        - **Service Provider Binding**: select **Post**
    - **Advanced protocol settings**
        - **Signing Certificate**: select the appproriate certificate for Slack.
        - **Property mappings**: Select the property mappings that you created in Step 1. You can leave the default property mappings and other settings.
4. Click **Finish** to create the provider.

### Step 3. Create a new application

1. Navigate to **Applications -> Applications** and then click **Create**.
2. Provide a name for the new application.
3. Set the provider to the one you just created.
4. Click **Create**.

:::info
After you have created the provider and application, and the application is connected to the provider (Step 3 above) the **Overview** tab on the provider's detail page in the Admin UI will display additional information that you will need to configure Slack, using the following steps.
:::

## Slack configuration

### Step 4. Configure Slack

1. Log in to the Slack Admin Dashboard.
2. Navigate to the **Configure SAML Authentication** page.
3. Enter the following values:
    - **SAML 2.0 Endpoint (HTTP)**: copy/paste in the **SSO URL (Redirect)** URL from the provider that you created in authentik. **Example**: `https://_authentik.company_/applications/saml/slack/sso/binding/redirect/`
    - **Identity Provider Issuer**: set to `https://slack.com`
    - **Public Certificate**: add the certificate, which you can download from the authentik provider, under **Download signing certificate**.
4. Optionally, configure the other settings and customize the Sign in button label.
5. Click **Save**.
