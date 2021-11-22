---
title: Active Directory
---

## Preparation

The following placeholders will be used:

- `ad.company` is the Name of the Active Directory domain.
- `authentik.company` is the FQDN of the authentik install.

## Active Directory setup

1. Open Active Directory Users and Computers

2. Create a user in Active Directory, matching your naming scheme

    ![](./01_user_create.png)

3. Give the User a password, generated using for example `pwgen 64 1` or `openssl rand -base64 36`.

4. Open the Delegation of Control Wizard by right-clicking the domain and selecting "All Tasks".

5. Select the authentik service user you've just created.

6. Ensure the "Reset user password and force password change at next logon" Option is checked.

    ![](./02_delegate.png)

7. Grant these additional permissions (only required when *Sync users' password* is enabled, and dependent on your AD Domain)

    ![](./03_additional_perms.png)

Additional infos: https://support.microfocus.com/kb/doc.php?id=7023371

## authentik Setup

In authentik, create a new LDAP Source in Resources -> Sources.

Use these settings:

- Server URI: `ldap://ad.company`

    For authentik to be able to write passwords back to Active Directory, make sure to use `ldaps://`

- Bind CN: `<name of your service user>@ad.company`
- Bind Password: The password you've given the user above
- Base DN: The base DN which you want authentik to sync
- Property mappings: Control/Command-select all Mappings which start with "authentik default LDAP" and "authentik default Active Directory"
- Group property mappings: Select "authentik default LDAP Mapping: Name"

The other settings might need to be adjusted based on the setup of your domain.

- Addition User/Group DN: Additional DN which is _prepended_ to your Base DN for user synchronization.
- Addition Group DN: Additional DN which is _prepended_ to your Base DN for group synchronization.
- User object filter: Which objects should be considered users.
- Group object filter: Which objects should be considered groups.
- Group membership field: Which user field saves the group membership
- Object uniqueness field: A user field which contains a unique Identifier
- Sync parent group: If enabled, all synchronized groups will be given this group as a parent.

After you save the source, a synchronization will start in the background. When its done, you cen see the summary on the System Tasks page.

![](./10_ak_status.png)

To finalise the Active Directory setup, you need to enable the backend "authentik LDAP" in the Password Stage.

![](./11_ak_stage.png)
