---
title: Integrate with Veeam Backup & Replication
sidebar_label: Veeam Backup & Replication
support_level: community
---

import SAMLProvider20265Warning from "../../\_saml-provider-2026-5-warning.mdx";

## What is Veeam Backup & Replication?

> Veeam Backup & Replication is a comprehensive data protection and disaster recovery solution. It enables image-level backups of virtual, physical, and cloud workloads and supports flexible restore options across the entire environment.
>
> -- https://www.veeam.com/products/veeam-data-platform/backup-recovery.html

## Preparation

The following placeholders are used in this guide:

- `vbr.company` is the FQDN of the Veeam Backup & Replication server.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

You need one or more existing groups in authentik to assign roles in Veeam Backup & Replication.

## authentik configuration

To support the integration of Veeam Backup & Replication with authentik, you need to download the Veeam Backup & Replication service provider metadata and then create an application/provider pair in authentik.

### Download the service provider metadata

1. Log in to the Veeam Backup & Replication console as an administrator.
2. From the main menu, select **Users & Roles**.
3. Open the **Identity Provider** tab.
4. Select **Enable SAML authentication**.
5. Under **Service Provider (SP) information**, click **Install** to select a valid Veeam Backup & Replication server certificate.
6. Under **Service Provider (SP) information**, click **Download** to save the service provider metadata XML file. You will upload this file to authentik in the next section.

### Create an application and provider

<SAMLProvider20265Warning />

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **SAML Provider from Metadata** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configuration:
        - **Metadata**: select the SP metadata XML you downloaded from Veeam Backup & Replication during the pre-configuration step.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.
4. Navigate to **Applications** > **Providers** and click the provider you created.
5. Open the **Metadata** tab and click **Download** to save the identity provider metadata XML file.

## Veeam Backup & Replication configuration

1. Switch back to the Veeam Backup & Replication console and reopen **Users & Roles** > **Identity Provider**.
2. Under **Identity provider (IdP) information**, click **Browse** and select the metadata XML you downloaded from authentik in the previous step.
3. Click **OK** to save the SAML configuration.

### Map authentik groups to Veeam roles

To grant access to a user, the authentik group the user belongs to must be mapped to a Veeam role.

1. In the Veeam Backup & Replication console, open **Users & Roles** and switch to the **Security** tab.
2. Click **Add** > **External user or group**.
3. From the **Type** menu, select **Group**.
4. In the **Name** field, enter the name of the authentik group whose members should be granted the role.
5. From the **Role** menu, select the role that you want to assign to members of this group.
6. Click **OK** to save the role mapping.

:::info Group names
The group name that you enter in Veeam Backup & Replication must match the authentik group name.
:::

## Configuration verification

To confirm that authentik is properly configured with Veeam Backup & Replication, log out of the Veeam Backup & Replication console and click **Sign in with SSO** on the sign-in screen. You should be redirected to authentik to log in, then redirected back to the Veeam Backup & Replication console.

## Resources

- [Veeam Help Center - SAML Authentication](https://helpcenter.veeam.com/docs/vbr/userguide/identity_provider.html?ver=13)
- [Veeam Help Center - Logging in to Veeam Backup & Replication](https://helpcenter.veeam.com/docs/vbr/userguide/logon_to_console.html)
