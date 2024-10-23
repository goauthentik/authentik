---
title: Integrate with VMware vCenter
sidebar_label: VMware vCenter
---

# VMware vCenter

<span class="badge badge--secondary">Support level: Community</span>

## What is vCenter

> vCenter Server is the centralized management utility for VMware, and is used to manage virtual machines, multiple ESXi hosts, and all dependent components from a single centralized location. VMware vMotion and svMotion require the use of vCenter and ESXi hosts.
>
> -- https://en.wikipedia.org/wiki/VCenter

:::caution
Integration with authentik requires VMware vCenter 8.03 or newer.
:::

:::note
The vCenter still needs to be joined to the Active Directory Domain, otherwise group membership does not work correctly. We're working on a fix for this, for the meantime your vCenter should be part of your Domain.
:::

## Preparation

The following placeholders will be used:

-   `vcenter.company` is the FQDN of the vCenter server.
-   `authentik.company` is the FQDN of the authentik install.

Since vCenter only allows OpenID-Connect in combination with Active Directory/LDAP, it is recommended to have authentik sync with the same Active Directory. You also have the option of connecting to an authentik-managed LDAP outpost for user management.

## authentik configuration

### Step 1

Under _Customization_ -> _Property Mappings_, create a _Scope Mapping_. Give it a name like "OIDC-Scope-VMware-vCenter". Set the scope name to `openid` and the expression to the following

```python
return {
  "domain": "<your active directory domain>",
}
```

If you are using an authentik-managed LDAP outpost you can use the following expression in your property mapping. This will correctly return the `groups` claim as a list of LDAP DNs instead of their names.

```python
ldap_base_dn = "DC=ldap,DC=goauthentik,DC=io"
groups = []
for group in request.user.ak_groups.all():
    group_dn = f"CN={group.name},dc=groups,{ldap_base_dn}"
    groups.append(group_dn)
return {
    "name": request.user.name,
    "email": request.user.email,
    "given_name": request.user.name,
    "preferred_username": request.user.username,
    "nickname": request.user.username,
    "groups": groups,
    "domain": "ldap.goauthentik.io"
}
```

### Step 2

:::note
If your Active Directory Schema is the same as your Email address schema, skip to Step 3.
:::

Under _Sources_, click _Edit_ and ensure that `authentik default Active Directory Mapping: userPrincipalName` has been added to your source.

### Step 3

Create an application and an OAuth2/OpenID provider, using the authentik Wizard.

1. Log into authentik as an admin, and navigate to **Applications --> Applications**, and then click **Create with Wizard**.

2. In the Wizard, follow the prompts to create an application and its provider.

Create the application with these settings:

-   Select OIDC as the provider type.
-   Ensure that the **Redirect URI Setting** is left empty.

Create the provider with these settings:

-   Redirect URI: `https://vcenter.company/ui/login/oauth2/authcode`
-   Ensure that the signing key is provided (or you accept the default to authentik's Self-signed Certificate).

3. Click **Submit** to create the application and provider, and then click **Close** to close the Wizard.

Optionally, you can use a policy to apply access restrictions to the application.

## vCenter Setup

1. Log in to VCenter with your local Administrator account. Using the menu in the left navigation bar, navigate to _Administration -> Single Sing-on -> Configuration_.

2. Click _Change Provider_ in the top-right corner, and then select **Okta** from the drop-down list.

3. In the wizard, click **RUN PRECHECKS**, select the confirmation box, and then click **Next**.

    - Enter the Directory Name, for example `authentik.company` or any other name.
    - Add a Domain Name, for example `authentik.company`.
    - Click on the Plus (+) sign to show the default domain name.

4. Click **Next**.

5. On the OpenID Connect page, enter the following values:

    - Set `Identity Provider Name` to `authentik`.
        - Set `Client Identifier` to the client ID from authentik.

-   Set `Shared secret` to the client secret from authentik.
    -   Set `OpenID Address` to the _OpenID Configuration URL_ from authentik.

6. Click **Next**, and then **Finish**.

7. On the **Single Sign On -> Configuration** page, in the `User Provisioning` area, take the following steps:

    - Copy the **Tenant URL** and save to a safe place.
    - Click on `Generate` to generate a SCIM token.
    - Click **Generate** in the newly opened modal box.
    - Copy the token and save to a safe place.

8. Return to the authentik Admin interface.

    - Create a SCIM provider with the name `vcenter-scim`.
    - Paste the Tenant URL into URL field for the provider.
    - Paste the token you saved into the Token field.
    - Check verify certificate setting (note: not merged yet)
    - Configure options under `User filtering` to your needs.
    - Save the provider.
    - Edit the application that you created earlier and select this newly created SCIM provider as backchannel provider.
    - Navigate to the provider and trigger a sync.

9. Return to VCenter.

    - Navigate to **Administration -> Access Control -> Global Permissions**.
    - Click **Add**.
    - Select the Domain created above from the dropdown.
    - Enter the name of the group to which you want to assign permissions.
    - Select the role.

10. Click **Save**.
