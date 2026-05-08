---
title: Service accounts
sidebar_label: Service accounts
---

Service accounts are specialized user accounts designed for machine-to-machine authentication and automation purposes rather than interactive human use. They're ideal for integrating authentik with external systems, APIs, and services.

## Types of service accounts

authentik distinguishes between two types of service accounts:

1. **User-created service accounts**: Created by administrators for integrating with external systems or for automation purposes.
2. **Internal service accounts**: Created and managed automatically by authentik for internal purposes, such as outpost communications. These cannot be created manually.

## Limitations

Service accounts have certain limitations compared to regular user accounts:

1. Cannot log in through the UI.
2. Cannot have a password (they use tokens exclusively).
3. Cannot participate in multi-factor authentication flows.
4. Cannot be used for interactive sessions that require human interaction.
5. Cannot have permissions assigned directly if they are internal service accounts.
6. Cannot change their own password or manage their own account settings.
7. Are subject to token expiration policies that differ from regular user accounts.

## Create a service account

To create a service account:

1. In the authentik **Admin interface**, navigate to **Directory** > **Users**.
2. Click the **Create Service Account** button.
3. Configure the following settings:
    - **Username**: The user's primary identifier (150 characters or fewer).
    - **Create Group**: Enabling this toggle will create a group named after the user, with the user as a member.
    - **Expiring**: If selected, the token will expire and be automatically rotated upon expiration.
    - **Expires on**: Sets the expiration date (defaults to 1 year from the creation date).
4. Click **Create Service Account**.

After creating the service account, you'll see a confirmation screen that shows the username and generated password (token). Make sure to copy this information somewhere secure because you'll need it for authentication.

## Token properties

Service account tokens have the following properties:

- **Expiration**: By default, tokens expire after 360 days but can be configured to be non-expiring.
- **Custom Expiration Date**: You can set a specific expiration date when creating the service account.
- **Revocation**: Tokens can be revoked at any time by deleting them or generating new ones. OAuth2 access tokens associated with service accounts can also be introspected or revoked through the OAuth2 provider endpoints when the authenticating provider is the issuing provider or is configured for [cross-provider token introspection and revocation](../add-secure-apps/providers/oauth2/index.mdx#cross-provider-token-introspection-and-revocation).
- **Automatic Rotation**: When a token expires, it's automatically rotated to maintain security.

## Manage service account tokens

Tokens for service accounts are managed through the authentik Admin interface:

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Tokens and App passwords**.
   Here you can view, create, copy, delete, and manage tokens.

### Create new tokens

To create a new token for a service account:

1. Click **Create**.
2. Set the identifier for your token.
3. In the **User** dropdown list, select your service account.
4. For **Intent**, choose one of the following:
    - **API Token**: Used to access the API programmatically (30-minute default lifespan).
    - **App password**: Used for logging in using a flow executor (1-year default lifespan).
5. Click **Create** to generate the new token.

### Manage and regenerate tokens

- To copy a token's value, use the copy button under the **Actions** column.
- To delete a token, select it from the list and click the **Delete** button.
- To regenerate a token, delete the existing token and create a new one with the same settings, ensuring you select the same username under the **User** dropdown list.

## Authentication with service accounts

Service accounts authenticate using [HTTP Basic authentication](https://datatracker.ietf.org/doc/html/rfc7617). The username and password (token) generated during account creation are used as credentials.

## Permissions and access control

Like regular user accounts, with service accounts you can assign [permissions and use RBAC](../users-sources/access-control/manage_permissions.md).

1. Assign the service account to groups to inherit group permissions.
2. Grant specific permissions directly to the service account.
3. Restrict the service account to specific applications or resources.

We recommend following the principle of least privilege and granting service accounts only the permissions they need.

## Common use cases

### Integration with external systems

Service accounts are commonly used for:

1. **LDAP authentication**: Systems like SSSD, QNAP NAS, and other LDAP clients often use service accounts to bind to authentik's LDAP provider.
2. **Directory synchronization**: Tools that sync users and groups between authentik and other systems.
3. **API automation**: For scripts, CI/CD pipelines, or other systems that need to interact with authentik's API.

## Security best practices

When using service accounts, follow these security practices:

1. **Least privilege**: Grant service accounts only the permissions they need.
2. **Secure storage**: Store service account tokens securely in encrypted storage, environment variables, or secret management systems.
3. **Token rotation**: Rotate tokens periodically for sensitive integrations.
4. **Use expiration**: Set appropriate token expiration dates for your use case.
5. **Audit usage**: Monitor service account activity for unexpected behavior.
