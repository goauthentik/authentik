---
title: FreeIPA
support_level: community
---

## Preparation

The following placeholders are used in this guide:

- `svc_authentik` is the name of the bind account.
- `freeipa.company` is the Name of the domain.
- `ipa1.freeipa.company` is the Name of the FreeIPA server.

## FreeIPA Setup

1. Log into FreeIPA.

2. Create a user in FreeIPA, matching your naming scheme. Provide a strong password, example generation methods: `pwgen 64 1` or `openssl rand 36 | base64 -w 0`. After you are done click **Add and Edit**.

    ![](./01_user_create.pn)

3. In the user management screen, select the Roles tab.

    ![](./02_user_roles.png)

4. Add a role that has privileges to change user passwords, the default `User Administrators` role is sufficient. This is needed to support password resets from within authentik.

    ![](./03_add_user_role.png)

5. By default, if an administrator account resets a user's password in FreeIPA the user's password expires after the first use and must be reset again. This is a security feature to ensure password complexity and history policies are enforced. To bypass this feature for a more seamless experience, you can make the following modification on each of your FreeIPA servers:

    ```
    $ ldapmodify -x -D "cn=Directory Manager" -W -h ipa1.freeipa.company -p 389

    dn: cn=ipa_pwd_extop,cn=plugins,cn=config
    changetype: modify
    add: passSyncManagersDNs
    passSyncManagersDNs: uid=svc_authentik,cn=users,cn=accounts,dc=freeipa,dc=company
    ```

Additional info: [22.1.2. Enabling Password Reset Without Prompting for a Password Change at the Next Login](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/linux_domain_identity_authentication_and_policy_guide/user-authentication#user-passwords-no-expiry)

## authentik Setup

In authentik, create a new LDAP Source in Directory -> Federation & Social login.

Use these settings:

- Server URI: `ldaps://ipa1.freeipa.company`

    You can specify multiple servers by separating URIs with a comma, like `ldap://ipa1.freeipa.company,ldap://ipa2.freeipa.company`.

    When using a DNS entry with multiple Records, authentik will select a random entry when first connecting.

- Bind CN: `uid=svc_authentik,cn=users,cn=accounts,dc=freeipa,dc=company`
- Bind Password: The password you've given the user above
- Base DN: `dc=freeipa,dc=company`
- Property mappings: Control/Command-select all Mappings which start with "authentik default LDAP" and "authentik default OpenLDAP"
- Group property mappings: Select "authentik default OpenLDAP Mapping: cn"

Additional settings:

- Group: If selected, all synchronized groups will be given this group as a parent.
- Addition User/Group DN: `cn=users,cn=accounts`
- Addition Group DN: `cn=groups,cn=accounts`
- User object filter: `(objectClass=person)`
- Group object filter: `(objectClass=groupofnames)`
- Group membership field: `member`
- Object uniqueness field: `ipaUniqueID`

    ![](./04_source_settings_1.png)
    ![](./05_source_settings_2.png)

After you save the source, you can kick off a synchronization by navigating to the source, clicking on the "Sync" tab, and clicking the "Run sync again" button.

![](./06_sync_source.png)

Lastly, verify that the "User database + LDAP password" backend is selected in the "Password Stage" under Flows -> Stages.

![](./07_password_stage.png)
