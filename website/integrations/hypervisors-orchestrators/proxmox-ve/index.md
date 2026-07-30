---
title: Integrate with Proxmox VE
sidebar_label: Proxmox VE
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Proxmox VE?

> Proxmox VE is an open-source virtualization platform for managing virtual machines, containers, storage, and networks from a web interface or CLI.
>
> -- https://www.proxmox.com/en/products/proxmox-virtual-environment

## Preparation

The following placeholders are used in this guide:

- `proxmox.company` is the FQDN of the Proxmox VE installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Proxmox VE with authentik, you need to create an application/provider pair in authentik. If you want Proxmox VE to map permissions from OIDC group data, you can also create application entitlements.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the application **Slug**, because it will be required later.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations:
    - Note the **Client ID** and **Client Secret** values because they will be required later.
    - Add a **Redirect URI** of type `Strict` `Authorization` as `https://proxmox.company:8006`.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

### Create application entitlements _(optional)_

Use [application entitlements](/docs/add-secure-apps/applications/manage_apps/#application-entitlements) if you want authentik to send Proxmox VE group values for permission mapping.

1. Open the Proxmox VE application in authentik.
2. Click the **Application entitlements** tab.
3. Create entitlements for the Proxmox VE groups that authentik should send, then bind each entitlement to the appropriate users or groups. Use Proxmox VE-compatible group names, such as `pve-admins`.
4. Navigate to **Applications** > **Providers**.
5. Select your provider for Proxmox VE and click **Edit**.
6. Under **Advanced protocol settings** > **Selected Scopes**, add `authentik default OAuth Mapping: OpenID 'entitlements'`.
7. Click **Update**.

Proxmox VE appends `-<realm_name>` to OIDC group names. For example, with a Proxmox VE realm named `authentik`, an entitlement named `pve-admins` is mapped as the Proxmox VE group `pve-admins-authentik`.

## Proxmox VE configuration

### Configure the realm in the web interface

1. Log in to the Proxmox VE web interface using an administrative account.
2. Navigate to **Datacenter** > **Permissions** > **Realms**.
3. Click **Add** and select **OpenID Connect Server**.
4. Configure the following settings:
    - **Issuer URL**: `https://authentik.company/application/o/<application_slug>/`
    - **Realm**: enter a name for this authentication source, such as `authentik`.
    - **Client ID**: enter the **Client ID** from the authentik provider.
    - **Client Key**: enter the **Client Secret** from the authentik provider.
    - **Username Claim**: select `username`.
    - **Autocreate Users**: enable this option if Proxmox VE should create users during their first login.
    - **Default**: enable this option if this realm should be pre-selected on the login screen.
5. If you created application entitlements for Proxmox VE group mapping, also configure the following settings:
    - **Scopes**: `email profile entitlements`
    - **Groups Claim**: `entitlements`
    - **Autocreate Groups**: enable this option if Proxmox VE should create groups during login when they do not already exist.
6. Click **Add** to save the realm.

### Configure the realm with the CLI _(optional)_

To configure the OpenID Connect realm from the CLI, SSH into any Proxmox VE cluster node and run the following command:

```bash
pveum realm add authentik \
    --type openid \
    --issuer-url https://authentik.company/application/o/<application_slug>/ \
    --client-id "<Client ID from authentik>" \
    --client-key "<Client Secret from authentik>" \
    --username-claim username \
    --autocreate 1
```

If you created application entitlements for Proxmox VE group mapping, add the following options to the command:

```bash
--scopes "email profile entitlements" --groups-claim entitlements --groups-autocreate 1
```

### Assign permissions

After the realm is configured, go to **Datacenter** > **Permissions** and assign roles to the users or groups that should access Proxmox VE resources.

## Configuration verification

To verify the integration of authentik with Proxmox VE, log out of Proxmox VE, select the authentik realm on the login page, and sign in. If you set the authentik realm as the default, it is automatically selected on the login page.

## Resources

- [Proxmox VE documentation - User Management](https://pve.proxmox.com/pve-docs/chapter-pveum.html)
- [Proxmox VE documentation - pveum](https://pve.proxmox.com/pve-docs/pveum.1.html)
- [Proxmox VE source - OpenID authentication plugin](https://github.com/proxmox/pve-access-control/blob/master/src/PVE/Auth/OpenId.pm)
- [Proxmox VE source - OpenID realm form](https://github.com/proxmox/pve-manager/blob/master/www/manager6/dc/AuthEditOpenId.js)
