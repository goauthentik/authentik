---
title: Integrate with Veeam Backup & Replication
sidebar_label: Veeam Backup & Replication
support_level: community
---

## What is Veeam Backup & Replication?

> Veeam Backup & Replication is a comprehensive data protection and disaster recovery solution. It enables image-level backups of virtual, physical, and cloud workloads and supports flexible restore options across the entire environment.
>
> -- https://www.veeam.com/products/veeam-data-platform/backup-recovery.html

This guide was tested with Veeam Backup & Replication 13.0.1 and authentik 2026.5.0.

## Preparation

The following placeholders are used in this guide:

- `vbr.company` is the FQDN of the Veeam Backup & Replication server.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

You will need one or more existing groups in authentik to assign roles in Veeam Backup & Replication.

## Veeam Backup & Replication pre-configuration

1. Log in to the Veeam Backup & Replication console as an administrator.
2. From the main menu, click **Users and Roles**.
3. Open the **Identity Provider** tab.
4. Check **Enable SAML authentication**.
5. Under **Backup server configuration**, click **Download** to save the service provider metadata XML file. You will upload this file to authentik in the next section.

## authentik configuration

To support the integration of Veeam Backup & Replication with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application Name**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **SAML Provider from Metadata** as the provider type.
    - **Configure the Provider**: provide the following required configurations.
        - **Provider Name**: a descriptive name (or accept the auto-provided name).
        - **Authorization Flow**: the authorization flow to use for this provider.
        - **Invalidation Flow**: the flow to use when logging out of this provider.
        - **Metadata**: click **Choose File** and select the SP metadata XML you downloaded from Veeam Backup & Replication during the pre-configuration step. The ACS URL and SP Entity ID are imported from this file.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

4. Locate the new SAML provider in the provider list and click **Download Metadata** to save the identity provider metadata XML file.

## Veeam Backup & Replication configuration

1. Switch back to the Veeam Backup & Replication console and reopen **Users and Roles** > **Identity Provider**.
2. Under **Identity provider configuration**, click **Browse...** next to **IdP metadata file** and select the metadata XML you downloaded from authentik in the previous step.
3. Click **OK** to save the SAML configuration.

### Map authentik groups to Veeam roles

To grant access to a user, the authentik group the user belongs to must be mapped to a Veeam role.

1. In the Veeam Backup & Replication console, open **Users and Roles** and switch to the **Roles** tab.
2. Click **Add...** and select **External Group**.
3. Enter the name of the authentik group whose members should be granted the role, and select the desired Veeam role.
4. Click **OK** to save the role mapping.

## Configuration verification

To confirm that authentik is properly configured with Veeam Backup & Replication, log out of the Veeam Backup & Replication console and click **Single sign-on** on the sign-in screen. You should be redirected to authentik to log in, then redirected back to the Veeam Backup & Replication console.
