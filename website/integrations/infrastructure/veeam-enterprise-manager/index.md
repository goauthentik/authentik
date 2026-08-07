---
title: Integrate with Veeam Enterprise Manager
sidebar_label: Veeam Enterprise Manager
support_level: community
---

import SAMLProvider20265Warning from "../../\_saml-provider-2026-5-warning.mdx";

## What is Veeam Enterprise Manager?

> Veeam Backup Enterprise Manager (Enterprise Manager) is a management and reporting component that allows you to manage multiple Veeam Backup & Replication installations from a single web console. Veeam Backup Enterprise Manager helps you optimize performance in remote office/branch office (ROBO) and large-scale deployments and maintain a view of your entire virtual environment.
>
> -- https://helpcenter.veeam.com/docs/backup/em/introduction.html

## Preparation

The following placeholders are used in this guide:

- `veeam.company` is the FQDN of the Veeam Enterprise Manager installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

You will need one or more existing groups in authentik to assign roles in Veeam Enterprise Manager.

## authentik configuration

To support the integration of Veeam Enterprise Manager with authentik, you need to download the Veeam Enterprise Manager service provider metadata and then create an application/provider pair in authentik.

### Download the service provider metadata

1. Log in to Veeam Enterprise Manager as an administrator.
2. In the top-right corner, click **Configuration**.
3. In the left sidebar, select **Settings**, then open the **SAML Authentication** tab.
4. Select **Enable SAML 2.0**.
5. Click **Download** to save the service provider metadata XML file. You will upload this file to authentik in the next section.

### Create an application and provider

<SAMLProvider20265Warning />

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **SAML Provider from Metadata** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configuration:
        - **Metadata**: select the service provider metadata XML you downloaded from Veeam Enterprise Manager in the previous section.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.
4. Navigate to **Applications** > **Providers** and click the provider you created.
5. Open the **Metadata** tab and click **Download** to save the identity provider metadata XML file.

## Veeam Enterprise Manager configuration

1. Switch back to Veeam Enterprise Manager and reopen **Configuration** > **Settings** > **SAML Authentication**.
2. Click **Import from File** and select the identity provider metadata XML file that you downloaded from authentik.
3. Make sure that **Enable SAML 2.0** is still selected.
4. Click **Save**.

### Map authentik groups to Veeam Enterprise Manager roles

To grant access to a user, the authentik group the user belongs to must be mapped to a Veeam Enterprise Manager role.

1. In Veeam Enterprise Manager, navigate to **Configuration** > **Roles**.
2. Click **Add...** and select **External Group**.
3. Enter the name of the authentik group whose members should be granted access.
4. Select the role that you want to assign to members of this group.
5. Click **OK** to save the role mapping.

:::info Group names
The group name that you enter in Veeam Enterprise Manager must match the authentik group name.
:::

## Configuration verification

To confirm that authentik is properly configured with Veeam Enterprise Manager, log out of Veeam Enterprise Manager and click **Sign in with SSO** on the sign-in screen. You should be redirected to authentik to log in, then redirected back to Veeam Enterprise Manager.

## Resources

- [Veeam Help Center - SAML Authentication Support](https://helpcenter.veeam.com/docs/vbr/em/em_saml.html)
- [Veeam Help Center - Configuring SAML Authentication Settings](https://helpcenter.veeam.com/docs/vbr/em/veeam_backup_em_saml.html)
- [Veeam Help Center - Accessing Enterprise Manager](https://helpcenter.veeam.com/docs/vbr/em/accessing_management_website.html)
