---
title: Integrate with Veeam Enterprise Manager
sidebar_label: Veeam Enterprise Manager
support_level: community
---

## What is Veeam Enterprise Manager

> Veeam Backup Enterprise Manager (Enterprise Manager) is a management and reporting component that allows you to manage multiple Veeam Backup & Replication installations from a single web console. Veeam Backup Enterprise Manager helps you optimize performance in remote office/branch office (ROBO) and large-scale deployments and maintain a view of your entire virtual environment.
>
> -- https://helpcenter.veeam.com/docs/backup/em/introduction.html

## Preparation

The following placeholders are used in this guide:

- `veeam.company` is the FQDN of the Veeam Enterprise Manager installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

You will need an existing group or multiple in authentik to assign roles in Veeam Enterprise Manager to.

## Veeam Enterprise Manager pre-configuration

Login to your Veeam Enterprise Manager. Navigate to the Configuration in the top-right. On the left sidebar, select Settings. Select the SAML Authentication tab.

Check the checkbox called "Enable SAML 2.0". Further down the site, click the "Download" button, to download the metadata.

## authentik configuration

To support the integration of Veeam Enterprise Manage with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click **Create** to create a provider.

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **slug** as it will be required later.
- **Choose a Provider type**: select **SAML Provider** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - todo: saml metadata
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

Go back to the Provider sidebar and locate the Veeam Enterprise Manager. Click the Download Metadata button.

## Veeam Enterprise Manager configuration

Back on Veeam Enterprise Manager, click on "Import from File", and select the XML file that you've downloaded from authentik. Make sure the "Enable SAML 2.0" checkbox is still enabled, and click save.

To map Veeam Enterprise Manager permissions to an authentik user, you have to create an External Group. In Veeam Enterprise Manager, under Configuration, navigate to Roles. Click the "Add..." button and select "External Group". Type in the name of a group you're member of.
