---
title: Integrate with VMware vCenter
sidebar_label: VMware vCenter
support_level: community
---

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

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of vCenter with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to `https://vcenter.company/ui/login/oauth2/authcode`.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

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
