---
title: Integrate with Oracle Cloud
sidebar_label: Oracle Cloud
support_level: community
---

## What is Oracle Cloud

> Oracle Cloud is the first public cloud built from the ground up to be a better cloud for every application. By rethinking core engineering and systems design for cloud computing, we created innovations that accelerate migrations, deliver better reliability and performance for all applications, and offer the complete services customers need to build innovative cloud applications.
>
> -- https://www.oracle.com/cloud/

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.
- `tenant.identity.oraclecloud.com` is the FQDN of your Oracle IDCS endpoint.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Oracle Cloud with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - Optionally set the **Launch URL** to `https://cloud.oracle.com?tenant=friendly-tenant-name` where `friendly-tenant-name` is the name of the tenant used when logging in via the [Oracle Cloud website](https://cloud.oracle.com).
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to `https://tenant.identity.oraclecloud.com/oauth2/v1/social/callback`.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Oracle Cloud configuration

To integrate authentik with Oracle Cloud, you must configure authentik as a social identity provider.

### Configure the identity provider

1. Log in to the Oracle Cloud dashboard as an administrator. Click the hamburger menu in the top-left corner, then select **Identity & Security** > **Domains**.
2. Select your domain and click **Federation**. Under **Actions**, choose **Add Social IdP**.
3. Set the following required information:
    - **Type**: `OpenID Connect`
    - **Name**: `authentik`
    - **Client ID**: set the client ID from authentik
    - **Client Secret**: set the client secret from authentik
    - **Discovery service URL**: `https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration`
    - **Enable Just-In-Time (JIT) provisioning**: toggle this on
4. Click **Add**. Then, click the three dots in the row of the identity provider that was just created. Click **Activate IdP**, read the confirmation message, and click **Activate IdP** again.

### Add to the login page

1. Log in to the Oracle Cloud dashboard as an administrator. Click the hamburger menu in the top-left corner, then select **Identity & Security** > **Domains**.
2. Select your domain and click **Federation**. Scroll down until you see the section called **Identity provider policies**.
3. Click your identity provider policy, or select the default policy named **Default Identity Provider Policy**.
4. Click the three dots, select **Edit IdP rule**, and under **Assign identity providers**, add `authentik`.
5. Save these changes.

## Configuration verification

To confirm that authentik is correctly configured with Oracle Cloud, log out of your current session. Then, try signing in by either selecting the application's icon in the User Library or by going directly to the Oracle Cloud login page, depending on your setup. On the login page, click **authentik**. You'll be redirected to authentik, and after a successful login, automatically signed in to Oracle Cloud.

## Resources

- [Oracle Cloud documentation - Add a Social Identity Provider](https://docs.oracle.com/en/cloud/paas/identity-cloud/uaids/add-social-identity-provider.html)
