---
title: Veeam Enterprise Manager
---

<span class="badge badge--secondary">Support level: Community</span>

## What is Veeam Enterprise Manager

> Veeam Backup Enterprise Manager (Enterprise Manager) is a management and reporting component that allows you to manage multiple Veeam Backup & Replication installations from a single web console. Veeam Backup Enterprise Manager helps you optimize performance in remote office/branch office (ROBO) and large-scale deployments and maintain a view of your entire virtual environment.
>
> -- https://helpcenter.veeam.com/docs/backup/em/introduction.html?ver=100

## Preparation

The following placeholders will be used:

-   `veeam.company` is the FQDN of the Veeam Enterprise Manager install.
-   `authentik.company` is the FQDN of the authentik install.

You will need an existing group or multiple in authentik to assign roles in Veeam Enterprise Manager to.

## In Veeam Enterprise Manager

Login to your Veeam Enterprise Manager. Navigate to the Configuration in the top-right. On the left sidebar, select Settings. Select the SAML Authentication tab.

Check the checkbox called "Enable SAML 2.0". Further down the site, click the "Download" button, to download the metadata.

## In authentik

Navigate to Providers in the sidebar. Click on the create dropdown, and select "SAML Provider from Metadata".

Give the provider a new, and selection an authorization flow. Select the XML file you just downloaded and confirm.

Now that you've created the provider, create an Application. Select the provider that has just been created. Set the launch URL to "https://veeam.company:9443/Saml2/SignIn" and confirm.

Click on the application to assign access policies.

Go back to the Provider sidebar and locate the Veeam Enterprise Manager. Click the Download Metadata button.

## Finish in Veeam Enterprise Manager

Back on Veeam Enterprise Manager, click on "Import from File", and select the XML file that you've downloaded from authentik. Make sure the "Enable SAML 2.0" checkbox is still enabled, and click save.

To map Veeam Enterprise Manager permissions to an authentik user, you have to create an External Group. In Veeam Enterprise Manager, under Configuration, navigate to Roles. Click the "Add..." button and select "External Group". Type in the name of a group you're member of.
