---
title: Integrate with VMware vCenter
sidebar_label: VMware vCenter
---

# Integrate with VMware vCenter

<span class="badge badge--secondary">Support level: Community</span>

## What is vCenter

> vCenter Server is the centralized management utility for VMware, and is used to manage virtual machines, multiple ESXi hosts, and all dependent components from a single centralized location. VMware vMotion and svMotion require the use of vCenter and ESXi hosts.
>
> -- https://en.wikipedia.org/wiki/VCenter

:::caution
Integration with authentik requires VMware vCenter 8.03 or newer.
:::

The following placeholders will be used in the examples below:

- `vcenter.company` is the FQDN of the vCenter server.
- `authentik.company` is the FQDN of the authentik installation.

## authentik configuration

Create an application and an OAuth2/OpenID provider, using the authentik Wizard.

1.  Log into authentik as an admin, and navigate to **Applications --> Applications**, and then click **Create with Wizard**.

2.  In the Wizard, follow the prompts to create an application and its provider.

    Create the application with these settings:

    - Select OIDC as the provider type.
    - Ensure that the **Redirect URI Setting** is left empty.

    Create the provider with these settings:

        -   Redirect URI: `https://vcenter.company/ui/login/oauth2/authcode`
        -   Ensure that a signing key is selected, for example the Self-signed Certificate.

3.  Click **Submit** to create the application and provider, and then click **Close** to close the Wizard.

Optionally, you can use a policy to apply access restrictions to the application.

## vCenter configuration

1. Log in to vCenter with your local Administrator account. Using the menu in the left navigation bar, navigate to **Administration -> Single Sign-on -> Configuration**.

2. Click **Change Provider** in the top-right corner, and then select **Okta** from the drop-down list.

3. In the wizard, click **Run Prechecks**, select the confirmation box, and then click **Next**

    - Enter the **Directory Name**. For example `authentik` or any other name.
    - Add a **Domain Name**. For example `authentik.company`.
    - Click on the Plus (+) sign to show the default domain name.

4. Click **Next**.

5. On the OpenID Connect page, enter the following values:

    - Set **Identity Provider Name** to `authentik`.
    - Set **Client Identifier** to the client ID from authentik.
    - Set **Shared secret** to the client secret from authentik.
    - Set **OpenID Address** to the _OpenID Configuration URL_ from authentik.

6. Click **Next**, and then **Finish**.

7. On the **Single Sign On -> Configuration** page, in the **User Provisioning** area, take the following steps:

    - Copy the **Tenant URL** and save to a safe place.
    - Click on **Generate** to generate a SCIM token.
    - Click **Generate** in the newly opened modal box.
    - Copy the token and save to a safe place.

8. Return to the authentik Admin interface.

    - Create a SCIM provider with the name `vcenter-scim`.
    - Paste the Tenant URL into **URL** field for the provider.
    - Paste the token you saved into the **Token** field.
    - If your vCenter certificate is self-signed (which is the default), toggle **Verify SCIM server's certificates** to be off.
    - Configure options under `User filtering` to your needs.
    - Save the provider.
    - Edit the application that you created earlier and select this newly created SCIM provider as the backchannel provider.
    - Navigate to the provider and trigger a sync.

9. Return to vCenter.

    - Navigate to **Administration -> Access Control -> Global Permissions**.
    - Click **Add**.
    - Select the Domain created above from the dropdown.
    - Enter the name of the group to which you want to assign permissions.
    - Select the role.

10. Click **Save**.
