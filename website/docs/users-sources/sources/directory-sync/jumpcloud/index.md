---
title: JumpCloud
---

authentik federates with [JumpCloud](https://jumpcloud.com/) through JumpCloud's **Cloud LDAP** service (LDAP-as-a-Service), using an LDAP source. Once configured, authentik synchronizes JumpCloud users and groups and can authenticate them against their JumpCloud credentials.

## Preparation

The following placeholders are used in this guide:

- `ldap.jumpcloud.com` is the JumpCloud Cloud LDAP endpoint (the same for all organizations).
- `authentik.company` is the FQDN of the authentik installation.
- `<ORG_ID>` is your JumpCloud Organization ID.
- `ldapservice` is the username of the JumpCloud user that authentik binds as.

## JumpCloud configuration

### 1. Enable Cloud LDAP and create a binding user

JumpCloud requires a dedicated user to bind to LDAP.

1. Log in to the [JumpCloud Admin Portal](https://console.jumpcloud.com/).
2. Navigate to **Identity Management** > **Users** and either select an existing user or create a new one (for example, `ldapservice`) to act as the bind account.
3. Open the user, and under **Details** > **User Security Settings and Permissions** > **Permission Settings**, enable **Enable as LDAP Bind DN**.
4. Save the user.

:::info
More than one user may be designated as an LDAP binding user. The binding user must also be bound to the LDAP directory (next step) in order to authenticate.
:::

### 2. Bind users and groups to the LDAP directory

Only users and groups that are explicitly bound to the LDAP directory are visible over Cloud LDAP.

1. Navigate to **Access** > **LDAP**.
2. Click the round + button in the top left, open the **User Groups** tab and bind the groups whose members authentik should synchronize. Binding a group grants all of its members access to the LDAP directory.
3. Open the **Users** tab and confirm that the accounts you expect to sync — including the `ldapservice` binding user — are present. Add any individual users that are not covered by a bound group.
4. Save your changes.
5. Note your JumpCloud **Organization ID**; it is used in the **Bind CN** and **Base DN** in the next section.

## authentik setup

To create a new LDAP source in authentik:

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login**, click **Create**, select **LDAP Source**, and click **Next**.
3. Provide a name and slug, and configure the following settings:

    Under **Connection settings**:
    - **Server URI**: `ldaps://ldap.jumpcloud.com`
    - **Enable StartTLS**: disable this option
    - **Bind CN**: `uid=ldapservice,ou=Users,o=<ORG_ID>,dc=jumpcloud,dc=com`
    - **Bind Password**: the password of the binding user created in the previous section.
    - **Base DN**: `ou=Users,o=<ORG_ID>,dc=jumpcloud,dc=com`

    Under **LDAP attribute mapping**:
    - **User Property Mappings**: select all mappings that start with `authentik default LDAP` and `authentik default OpenLDAP`, and remove any `authentik default Active Directory` mappings.
    - **Group Property Mappings**: set only `authentik default LDAP Mapping: Name`.

    Under **Additional settings**:
    - **User object filter**: `(objectClass=inetOrgPerson)`
    - **Group object filter**: `(objectClass=groupOfNames)`
    - **Object uniqueness field**: `uid`

4. Click **Finish** to save the LDAP source. An LDAP synchronization begins in the background.
