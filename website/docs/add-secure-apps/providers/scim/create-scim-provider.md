---
title: Create a SCIM provider
---

## Create a SCIM provider with token authentication

To create a provider along with a corresponding application, navigate to **Applications** > **Applications** and click **New Provider**. We recommend this combined approach for most common use cases. Alternatively, you can use the legacy method to solely create the provider by navigating to **Applications** > **Providers** and clicking **Create**.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to create an application and provider pair.
3. On the **Application** page, define the application settings, and then click **Next**.
4. Select **SCIM** as the **Provider Type**, and then click **Next**.
5. On the **Configure Provider** page, provide the configuration settings, and then click **Next**.
6. On the **Configure Bindings** page, click **Next**
7. Click **Create** to create both the application and the provider.

### Set the SCIM provider as a backchannel provider for the application

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click the edit icon of the new SCIM application.
3. Click the plus icon (+) next to **Backchannel providers**.
4. Select the new SCIM provider, and then click **Confirm**.
5. Click **Save changes**.

## Create a SCIM provider with OAuth authentication

There are 3 required steps to creating a SCIM provider:

1. [Create an OAuth source](#create-an-oauth-source)
2. [Create a SCIM application and provider](#create-a-scim-application-and-provider)
3. [Set the SCIM provider as a backchannel provider for the application](#set-the-scim-provider-as-a-backchannel-provider-for-the-application)

If using OAuth (Interactive) mode, you will also need to:

4. [Provide admin authorization](#provide-admin-authorization-oauth-interactive-mode-only)

### Create an OAuth source

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login** and click **New Source**.
3. Select **OpenID OAuth Source** as the **Source type**.
4. On the **OpenID OAuth Source Details** page, provide the configuration settings provided by the SCIM endpoint that you are provisioning to, and then click **Create**.

### Create a SCIM application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to create an application and provider pair.
3. On the **Application** page, define the application settings, and then click **Next**.
4. Select **SCIM** as the **Provider Type**, and then click **Next**.
5. On the **Configure Provider** page, configure the required settings. Set **Authentication mode** to the desired OAuth option, select the **OAuth source** you created in the previous section, and then click Next.
6. On the **Configure Bindings** page, click **Next**
7. Click **Create** to create both the application and the provider.

### Set the SCIM provider as a backchannel provider for the application

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click the edit icon of the new SCIM application.
3. Click the plus icon (+) next to **Backchannel providers**.
4. Select the new SCIM provider, and then click **Confirm**.
5. Click **Save changes**.

### Provide admin authorization (OAuth Interactive mode only)

If you selected **OAuth (Interactive)** as the **Authentication mode** for the SCIM provider, you will need to authorize the initial OAuth connection.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Proivders** and click the name of the new SCIM provider.
3. Next to **OAuth Status**, click **(Re-)Authenticate**.
4. You should be redirected to the SCIM endpoint that you are provisioning to for authentication.
5. Once authenticated you should be redirected back to authentik. If successful, **OAuth Status** should now show as **Authenticated**.
   This step is only required when initially configuring the SCIM provider. Subsequent authentications will be automatic.
