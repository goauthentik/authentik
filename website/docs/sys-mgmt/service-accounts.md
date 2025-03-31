---
title: Service Accounts
sidebar_label: Service Accounts
---

# Service Accounts

Service accounts are specialized user accounts designed for machine-to-machine authentication and automation purposes rather than interactive human use. They're ideal for integrating authentik with external systems, APIs, and services.

## Types of Service Accounts

authentik distinguishes between two types of service accounts:

1. **User-created Service Accounts**: Created by administrators for integrating with external systems or for automation purposes.
2. **Internal Service Accounts**: Created and managed automatically by authentik for internal purposes, such as outpost communications. These cannot be created manually.

## Creating a Service Account

To create a service account:

1. In the authentik **Admin interface**, navigate to **Directory** > **Users**.
2. Click the **Create Service Account** button.
3. Configure the following settings:
    - **Username**: The user's primary identifier (150 characters or fewer).
    - **Create Group**: Enabling this toggle will create a group named after the user, with the user as a member.
    - **Expiring**: If selected, the token will expire and be automatically rotated upon expiration.
    - **Expires on**: Sets the expiration date (defaults to 1 year from the creation date).
4. Click **Create Service Account**.

After creating the service account, you'll see a confirmation screen that shows the username and generated password (token). The password is a long, randomly generated string that will be valid for 360 days by default. Make sure to copy this information somewhere secure as you'll need it for authentication.

## Authentication with Service Accounts

Service accounts authenticate using [HTTP Basic Authentication](https://datatracker.ietf.org/doc/html/rfc7617). The username and password (token) generated during account creation are used as credentials.

## Managing Service Account Tokens

Tokens for service accounts can be managed through the authentik **Admin interface**:

1. Navigate to **Admin Interface** > **Directory** > **Tokens and App passwords**.
2. Here you can view, create, copy, delete, and manage tokens.

### Creating New Tokens

To create a new token for a service account:

1. Click **Create**.
2. Set the identifier for your token.
3. In the user dropdown, select your service account.
4. Under **Intent**, choose one of the following:
    - **API Token**: Used to access the API programmatically (30-minute default lifespan).
    - **App password**: Used for logging in using a flow executor (1-year default lifespan).
5. Click **Create** to generate the new token.

### Managing and Regenerating Tokens

- To copy a token's value, use the copy button under the **Actions** column.
- To delete a token, select it from the list and click the **Delete** button.
- To regenerate a token, delete the existing token and create a new one with the same settings, ensuring you select the same username under the User dropdown.

### Token Properties

- **Expiration**: By default, tokens expire after 360 days but can be configured to be non-expiring.
- **Custom Expiration Date**: You can set a specific expiration date when creating the service account.
- **Revocation**: Tokens can be revoked at any time by deleting them or generating new ones.
- **Automatic Rotation**: When a token expires, it's automatically rotated to maintain security.

## Permissions and Access Control

Like regular user accounts, with service accounts you can assign [permissions and use RBAC](../users-sources/access-control/manage_permissions).

1. Assign the service account to groups to inherit group permissions.
2. Grant specific permissions directly to the service account.
3. Restrict the service account to specific applications or resources.

We recommend following the principle of least privilege and only grant service accounts the permissions they absolutely need.

## Common Use Cases

### Integration with External Systems

Service accounts are commonly used for:

1. **LDAP Authentication**: Systems like SSSD, QNAP NAS, and other LDAP clients often use service accounts to bind to authentik's LDAP provider.
2. **Directory Synchronization**: Tools that sync users and groups between authentik and other systems.
3. **API Automation**: For scripts, CI/CD pipelines, or other systems that need to interact with authentik's API.

## Security Best Practices

When using service accounts, follow these security practices:

1. **Least Privilege**: Grant service accounts only the permissions they need.
2. **Secure Storage**: Store service account tokens securely in encrypted storage, environment variables, or secret management systems.
3. **Token Rotation**: Rotate tokens periodically for sensitive integrations.
4. **Use Expiration**: Set appropriate token expiration dates for your use case.
5. **Audit Usage**: Monitor service account activity for unexpected behavior.

## Limitations

Service accounts have certain limitations compared to regular user accounts:

1. Cannot log in through the UI.
2. Cannot have a password (they use tokens exclusively).
3. Cannot participate in multi-factor authentication flows.
4. Cannot be used for interactive sessions that require human interaction.
5. Cannot have permissions assigned directly if they are internal service accounts.
6. Cannot change their own password or manage their own account settings.
7. Are subject to token expiration policies that differ from regular user accounts.
