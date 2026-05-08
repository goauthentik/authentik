---
title: Service Accounts
sidebar_label: Service Accounts
---

Service accounts are specialized user accounts for machine-to-machine authentication and automation. Use them when an external service, script, integration, or protocol client needs to authenticate to authentik without representing a human user.

Common examples include LDAP bind users, automation that calls the authentik API, SCIM or outpost-related integrations, and third-party applications that need a stable credential.

## Types of service accounts

authentik has two service account types:

- **User-created service accounts**: accounts created by administrators for external systems or automation. These accounts appear under **Directory** > **Users** with the `Service account` user type.
- **Internal service accounts**: accounts created and managed by authentik for internal components, such as outpost communication. These accounts cannot be created manually, converted to another user type, or edited like regular users.

## How service accounts work

A user-created service account is an authentik user with the `Service account` type and an unusable password. Instead of a normal password, it authenticates with tokens:

- **App passwords** authenticate to flows and protocol clients that accept a username and password, such as LDAP bind clients. When you create a service account from **Directory** > **Users**, authentik creates an app password for the account and shows it once in the confirmation screen.
- **API tokens** authenticate to the authentik API with HTTP Bearer authentication. Use API tokens for scripts, CI/CD jobs, and other automation that calls `/api/v3/` endpoints.

A service account is still a user object for authorization purposes. You can add it to groups, add it to roles, assign object permissions, and include or exclude it from application access through bindings and policies.

## Limitations

Service accounts differ from regular users in the following ways:

- They are intended for non-interactive use and cannot access the authentik user or Admin interfaces. If a service account authenticates in a browser, authentik redirects it to the brand's default application when one is configured; otherwise access to the interface is denied.
- They do not have a usable account password. Use an app password or API token instead.
- They cannot complete interactive MFA setup or other human-driven account settings flows.
- They should not be used to represent a person. Create a regular internal or external user for human access.
- Internal service accounts are managed by authentik and cannot be modified directly.

## Create a service account

To create a service account:

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Users**.
3. Click **Create a service account**.
4. Configure the following settings:
    - **Username**: the primary identifier for the service account. This value is used as the username for app-password authentication.
    - **Create group**: creates a group with the same name as the service account and adds the service account to it. This can be useful when you want to grant access through group membership.
    - **Expiring**: controls whether the generated app password expires.
    - **Expires on**: sets the expiration date for the generated app password. If no date is provided, the default is 360 days.
5. Click **Create**.
6. Copy the generated username and password from the confirmation screen and store the password in a secure secret store.

:::warning
The generated password is the service account's initial app password. Treat it like any other secret. Anyone with this value can authenticate as the service account anywhere that app passwords are accepted.
:::

## Manage service account tokens

Service account tokens are managed from **Directory** > **Tokens and App passwords**.

### Create another app password

Create an app password when an integration needs username/password-style authentication, for example an LDAP bind password.

1. Navigate to **Directory** > **Tokens and App passwords**.
2. Click **Create**.
3. Enter a unique **Identifier**.
4. Select the service account in the **User** field.
5. Set **Intent** to **App password**.
6. Configure whether the token expires and, if needed, set **Expires on**.
7. Click **Create** and copy the generated value.

### Create an API token

Create an API token when automation needs to call the authentik API.

1. Navigate to **Directory** > **Tokens and App passwords**.
2. Click **Create**.
3. Enter a unique **Identifier**.
4. Select the service account in the **User** field.
5. Set **Intent** to **API Token**.
6. Click **Create** and copy the generated value.

Use the token as a Bearer token in the `Authorization` header when calling the authentik API:

```http
Authorization: Bearer <token>
```

### Rotate or revoke tokens

- To view a token value, use the copy action in **Directory** > **Tokens and App passwords**. Access to token values is controlled by the `View token's key` permission.
- To revoke a token, delete it.
- To rotate an app password, create a replacement token, update the external system, and then delete the old token.
- Expiring app passwords become invalid when they expire. Expiring API tokens are rotated by authentik.

## Permissions and access control

Service accounts start with no special access beyond normal authentication. Grant only the permissions required for the integration.

You can grant access in the same ways as regular users:

- Add the service account to a group and grant permissions to that group.
- Add the service account to a role and grant global or object permissions to that role.
- Grant object permissions directly to the service account when access should not be shared with other accounts.
- Use application [bindings](../add-secure-apps/applications/manage_apps.mdx#use-bindings-to-control-access) or policies to restrict which applications the service account can access.

For more information about assigning permissions, see [Manage permissions](../users-sources/access-control/manage_permissions.md).

### Example: LDAP search account

LDAP clients often need a bind account that can search the LDAP directory. In this case:

1. Create a service account, such as `ldapservice`.
2. Store the generated app password in the LDAP client configuration.
3. Create a role for LDAP search access.
4. Add the service account to that role.
5. On the LDAP provider, assign the role the **Search full LDAP directory** object permission.

For the full LDAP setup, see [Create an LDAP provider](../add-secure-apps/providers/ldap/create-ldap-provider.mdx#create-a-service-account).

### Example: API automation account

Automation that manages authentik objects should use an API token for a dedicated service account.

1. Create a service account for the automation, such as `ci-authentik-admin`.
2. Create an API token for that service account.
3. Grant the service account only the permissions required by the automation. For example, a script that rotates application certificates should receive certificate-related permissions, not full administrator access.
4. Store the API token in your CI/CD or secret management system and send it as `Authorization: Bearer <token>`.

## Security best practices

When using service accounts, follow these security practices:

- **Use one service account per integration**. Avoid sharing one account across unrelated systems so audit events and token rotation remain clear.
- **Grant least privilege**. Assign only the global permissions, object permissions, groups, roles, or application access that the integration needs.
- **Prefer expiring tokens** for credentials stored outside authentik, and rotate long-lived secrets on a regular schedule.
- **Store tokens securely** in a secret manager, encrypted environment variable store, or equivalent system.
- **Disable or delete unused accounts**. If an integration is retired, delete its tokens and deactivate or remove the service account.
- **Audit usage** by reviewing events for unexpected logins, API calls, or token access.
