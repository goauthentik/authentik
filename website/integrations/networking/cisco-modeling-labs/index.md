---
title: Integrate with Cisco Modeling Labs
sidebar_label: Cisco Modeling Labs
support_level: community
---

## What is Cisco Modeling Labs?

> Cisco Modeling Labs is an on-premises network simulation tool that runs on workstations and servers and allows you to quickly and easily simulate Cisco or multi-vendor networks.
>
> -- https://www.cisco.com/site/us/en/learn/training-certifications/training/modeling-labs/index.html

## Preparation

The following placeholders are used in this guide:

- `ldap.company` is the FQDN of the authentik LDAP outpost.

Cisco Modeling Labs (CML) authenticates users against LDAP. The CML server must be able to reach the authentik LDAP outpost on port 636.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Cisco Modeling Labs with authentik, you need to create groups for CML access, an LDAP application/provider pair, a service account, and an LDAP outpost.

### Create groups

Create groups that Cisco Modeling Labs uses to allow login and to grant administrator privileges. Users who should be CML administrators must be members of both groups, because CML requires an administrator to match both the user filter and the admin filter.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Groups** and click **Create**.
3. Set **Name** to `cml-users` and click **Create**.
4. Open the group, select the **Users** tab, and add the users who should have access to Cisco Modeling Labs.
5. Repeat these steps with the name `cml-admins`, and add only the users who should have CML administrator privileges. Also add those administrator users to `cml-users`.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **LDAP Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the bind flow to use for this provider, and note the **Base DN** because you will use it when configuring Cisco Modeling Labs.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

### Create a service account

1. Navigate to **Directory** > **Users** and click **New User**.
2. Select **Service Account**.
3. Set **Username** to `ldapservice` and disable **Expiring** so that the generated password does not rotate.
4. Click **Next**.
5. Copy the generated app password from the confirmation screen because it will be required later.

For an LDAP provider whose **Base DN** is `<base_dn>`, this service account's DN is `cn=ldapservice,ou=users,<base_dn>`.

### Assign LDAP search permissions

1. Navigate to **Directory** > **Roles** and click **Create**.
2. Provide a name, such as `LDAP search`, and click **Create**.
3. Click the role that you created and open the **Users** tab.
4. Click **Add Existing User**, select `ldapservice`, and click **Assign**.
5. Navigate to **Applications** > **Providers**.
6. Click the LDAP provider that you created and open the **Permissions** tab.
7. Click **Assign Object Permissions**.
8. Select the role that you created, enable **Search full LDAP directory**, and click **Assign**.

### Create an LDAP outpost

1. Navigate to **Applications** > **Outposts** and click **New Outpost**.
2. Configure the following settings:
    - **Name**: provide a descriptive name.
    - **Type**: select **LDAP**.
    - **Applications**: select the LDAP application that you created.
3. Click **Create**.

Expose the LDAP outpost as `ldap.company` so that Cisco Modeling Labs can reach it. If you already have an LDAP outpost, add this application to that outpost instead of creating a new one.

## Cisco Modeling Labs configuration

:::warning Incorrect LDAP settings
After you save LDAP as the authentication method, Cisco Modeling Labs authenticates every login against LDAP, including the local administrator account. Always use **Test Authentication** before you click **Save**. If you save incorrect settings and can no longer log in, recover access with the authentication reset in the CML system administration cockpit.
:::

1. Log in to Cisco Modeling Labs as a user with administrator privileges.
2. Navigate to **Tools** > **System Administration**.
3. Click **User Authentication**.
4. Set **Authentication Method** to `LDAP`.
5. Configure the following settings. Replace `<base_dn>` with the **Base DN** of the authentik LDAP provider.
    - **LDAP Servers**: `ldaps://ldap.company:636`
    - **Verify TLS**: enabled
    - **Root DN**: `<base_dn>`
    - **User Search Base**: `ou=users`
    - **User Filter**: `(&(cn={0})(memberOf=cn=cml-users,ou=groups,<base_dn>))`
    - **Admin Filter**: `(&(cn={0})(memberOf=cn=cml-admins,ou=groups,<base_dn>))`
    - **Group Search Base**: `ou=groups`
    - **Group Search Filter**: `(&(cn={0})(objectClass=group))`
    - **Group Via User**: enabled
    - **Group User Attribute**: `memberOf`
    - **Manager DN**: `cn=ldapservice,ou=users,<base_dn>`
    - **Manager Password**: the app password for the `ldapservice` service account
    - **Display Name LDAP Attribute**: `displayName`
    - **Email Address LDAP Attribute**: `mail`
6. If the LDAP outpost certificate is issued by a private CA, paste that CA certificate into **Certificate Chain**.
7. Click **Test Authentication**, enter the **Manager Password** if the field is empty, and test with an authentik username and password. **Authenticated** should be `true`. For a user in `cml-admins`, the test should also show that the admin filter matched.
8. Click **Save**.

### Create LDAP groups

Cisco Modeling Labs does not create groups from LDAP automatically. After you save the LDAP settings, create groups whose names match the authentik groups so that CML can synchronize membership on login.

1. Navigate to **Tools** > **System Administration**.
2. Click **Group Administration**.
3. Click **Add**.
4. Set the group name to `cml-users`, click **Next** through the optional wizard steps, and click **Create**.
5. Repeat these steps for `cml-admins`.

Do not add members in the wizard. CML reads group membership from authentik when each user logs in.

## Configuration verification

To confirm that authentik is properly configured with Cisco Modeling Labs, open the CML UI and log in with an authentik username and password. A user in `cml-users` should reach the CML dashboard.

## Resources

- [Cisco Modeling Labs documentation - Configuring LDAP Authentication](https://developer.cisco.com/docs/modeling-labs/configuring-ldap-authentication/)
- [Cisco Modeling Labs documentation - CML User Authentication](https://developer.cisco.com/docs/modeling-labs/cml-user-authentication/)
- [Cisco Modeling Labs documentation - Creating Groups](https://developer.cisco.com/docs/modeling-labs/creating-a-group/)
