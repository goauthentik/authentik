---
title: Configure an SSF provider
authentik_version: "2025.2.0"
description: "How to create and configure an SSF provider in authentik"
authentik_enterprise: true
authentik_preview: true
tags: [Shared Signals Framework, SSF, Apple Business Manager, backchannel]
---

Follow this workflow to create and configure an SSF provider for an application:

1. Create the SSF provider (which serves as the [backchannel provider](../../applications/manage_apps.mdx#backchannel-providers)).
2. Create an OIDC provider (which serves as the protocol provider for the application).
3. Create the application, and assign both the OIDC provider and the SSF provider.

## Create the SSF provider

1. Log in to authentik as an administrator, and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click **Create** to create a provider.
3. Select **Shared Signals Framework Provider** as the **Provider Type**, and then click **Next**.
4. On the **Create SSF Provider** page, provide the configuration settings. Be sure to select a **Signing Key**.
5. Click **Finish** to create the provider.

## Create the OIDC provider

1. Log in to authentik as an administrator, and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click **Create** to create a provider.
3. Select **OAuth2/OpenID Provider** as the **Provider Type**, and then click **Next**.
4. On the **Create OAuth2/OpenID Provider** page, provide the configuration settings and then click **Finish** to create the provider.

## Create the application

1. Log in to authentik as an administrator, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create** to create an application.
3. Configure the following required settings for the application:
    - **Name**: provide a descriptive name of the application.
    - **Slug**: provide the application slug used in URLs.
    - **Provider**: select the OIDC provider that you created.
    - **Backchannel Providers**: select the SSF provider that you created.
4. Click **Create** to save the new application.

The new application, with its OIDC provider and the backchannel SSF provider, should now appear in your application list.
