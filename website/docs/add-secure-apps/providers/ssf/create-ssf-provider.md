---
title: Configure an SSF provider
---

The workflow to implement an SSF provider as a [backchannel provider](../../applications/manage_apps#backchannel-providers) for an application/provider pair is as follows:

1. Create the SSF provider (which serves as the backchannel provider).
2. Create an OIDC provider (which serves as the protocol provider for the application).
3. Create the application, and assign both the OIDC provider and the SSF provider.

## Create the SSF provider

1. Log in to authentik as an admin, and in the Admin interface navigate to **Applications -> Providers**.

2. Click **Create**.

3. In the modal, select the **Provider Type** of **SSF**, and then click **Next**.

4. On the **New provider** page, provide the configuration settings. Be sure to select a **Signing Key**.

5. Click **Finish** to create and save the provider.

## Create the OIDC provider

1. Log in to authentik as an admin, and in the Admin interface navigate to **Applications -> Providers**.

2. Click **Create**.

3. In the modal, select the **Provider Type** of **OIDC**, and then click **Next**.

4. Define the settings for the provider, and then click **Finish** to save the new provider.

## Create the application

1. Log in to authentik as an admin, and in the Admin interface navigate to **Applications -> Applications**.

2. Click **Create**.

3. Define the settings for the application:

    - **Name**: define a descriptive name ofr the application.
    - **Slug**: optionally define the internal application name used in URLs.
    - **Group**: optionally select a group that you want to have access to this application.
    - **Provider**: select the OIDC provider that you created.
    - **Backchannel Providers**: select the SSF provider you created.
    - **Policy engine mode**: define policy-based access.
    - **UI Settings**: optionally define a launch URL, an icon, and other UI elements.

4. Click **Create** to save the new application.

The new application, with its OIDC provider and the backchannel SFF rpvier, should now appear in your list of Applications.
