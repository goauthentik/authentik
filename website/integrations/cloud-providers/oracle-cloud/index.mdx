---
title: Integrate with Oracle Cloud
sidebar_label: Oracle Cloud
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Oracle Cloud?

> Oracle Cloud is a cloud platform that provides infrastructure and platform services for running applications, storing data, and managing cloud resources.
>
> -- https://www.oracle.com/cloud/

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.
- `tenant.identity.oraclecloud.com` is the FQDN of your Oracle Cloud identity domain base URL.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Oracle Cloud with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
        - Note the application **Slug**, because it is required later.
        - Optionally set the **Launch URL** to `https://cloud.oracle.com?tenant=<tenant_name>`, where `<tenant_name>` is the tenant name used when logging in through the [Oracle Cloud sign-in page](https://cloud.oracle.com).
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they are required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://tenant.identity.oraclecloud.com/oauth2/v1/social/callback`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

## Oracle Cloud configuration

To integrate authentik with Oracle Cloud, configure authentik as a social identity provider in your Oracle Cloud identity domain.

### Configure the identity provider

1. Log in to the Oracle Cloud dashboard as an administrator. Click the hamburger menu in the top-left corner, then select **Identity & Security** > **Domains**.
2. Select your identity domain, click the **Federation** tab, and under **Actions**, select **Add Social IdP**.
3. Set the following required information:
    - **Type**: `OpenID Connect`
    - **Name**: `authentik`
    - **Client ID**: set the client ID from authentik.
    - **Client Secret**: set the client secret from authentik.
    - **Discovery service URL**: `https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration`
    - **Enable Just-In-Time (JIT) provisioning**: toggle this on.
4. Click **Add**.
5. Click the three dots in the row of the identity provider that was just created, select **Activate IdP**, read the confirmation message, and click **Activate IdP** again.

### Add the provider to an IdP policy

1. Log in to the Oracle Cloud dashboard as an administrator. Click the hamburger menu in the top-left corner, then select **Identity & Security** > **Domains**.
2. Select your identity domain. On the **Federation** tab, scroll to **Identity provider policies**. If your domain shows the current navigation instead, open **Security** > **IdP policies**.
3. Select your identity provider policy, or select the default policy named **Default Identity Provider Policy**.
4. Edit the rule that should offer authentik sign-in, and under **Assign identity providers**, add `authentik`.
5. Save the rule.

## Configuration verification

To confirm that authentik is properly configured with Oracle Cloud, open the Oracle Cloud integration from the authentik User interface. On the Oracle Cloud login page, click **authentik**. After you successfully log in with authentik, Oracle Cloud signs you in.

## Resources

- [Oracle Cloud documentation - Adding a Social Identity Provider](https://docs.oracle.com/en-us/iaas/Content/Identity/identityproviders/add-social-identity-provider.htm)
- [Oracle Cloud documentation - Listing Identity Provider Policies](https://docs.oracle.com/en-us/iaas/Content/Identity/idppolicies/list-idp-policies.htm)
