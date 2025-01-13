---
title: Active Directory
support_level: community
---

## Preparation

The following placeholders are used in this guide:

- `ad.company` is the Name of the Active Directory domain.
- `authentik.company` is the FQDN of the authentik install.

## Active Directory setup

1. Open Active Directory Users and Computers

2. Create a user in Active Directory, matching your naming scheme

    ![](./01_user_create.png)

3. Give the User a password, generated using for example `pwgen 64 1` or `openssl rand 36 | base64 -w 0`.

4. Open the Delegation of Control Wizard by right-clicking the domain and selecting "All Tasks".

5. Select the authentik service user you've just created.

6. Ensure the "Reset user password and force password change at next logon" Option is checked.

    ![](./02_delegate.png)

7. Grant these additional permissions (only required when _Sync users' password_ is enabled, and dependent on your AD Domain)

    ![](./03_additional_perms.png)

Additional info: https://support.microfocus.com/kb/doc.php?id=7023371

## authentik Setup

In authentik, create a new LDAP Source in Directory -> Federation & Social login.

Use these settings:

- Server URI: `ldap://ad.company`

    For authentik to be able to write passwords back to Active Directory, make sure to use `ldaps://`. You can test to verify LDAPS is working using `ldp.exe`.

    You can specify multiple servers by separating URIs with a comma, like `ldap://dc1.ad.company,ldap://dc2.ad.company`.

    When using a DNS entry with multiple Records, authentik will select a random entry when first connecting.

- Bind CN: `<name of your service user>@ad.company`
- Bind Password: The password you've given the user above
- Base DN: The base DN which you want authentik to sync
- Property mappings: Control/Command-select all Mappings which start with "authentik default LDAP" and "authentik default Active Directory"
- Group property mappings: Select "authentik default LDAP Mapping: Name"

Additional settings that might need to be adjusted based on the setup of your domain:

- Group: If enabled, all synchronized groups will be given this group as a parent.
- Addition User/Group DN: Additional DN which is _prepended_ to your Base DN configured above to limit the scope of synchronization for Users and Groups
- User object filter: Which objects should be considered users. For Active Directory set it to `(&(objectClass=user)(!(objectClass=computer)))` to exclude Computer accounts.
- Group object filter: Which objects should be considered groups.
- Group membership field: Which user field saves the group membership
- Lookup using user attribute: Lookup group memberships from a user object attribute instead of a group attribute (`memberOf` instead of `member`). It can be useful for looking up nested group memberships, for which you'd want to use `memberOf:1.2.840.113556.1.4.1941:` as the group membership field, to tell Active Directory to follow DNs.
- Object uniqueness field: A user field which contains a unique Identifier

After you save the source, a synchronization will start in the background. When its done, you can see the summary under Dashboards -> System Tasks.

![](./03_additional_perms.png)

To finalise the Active Directory setup, you need to enable the backend "authentik LDAP" in the Password Stage.

![](./11_ak_stage.png)
