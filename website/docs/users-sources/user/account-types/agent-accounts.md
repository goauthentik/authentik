---
title: Agent accounts
sidebar_position: 4
authentik_enterprise: true
authentik_version: "2026.8"
---

Agent accounts are service accounts that act on behalf of a parent user when calling the authentik API. Use them for automation, integrations, and other machine identities that need delegated access.

For an overview of all account types, see [Account types](./index.mdx). For general information about service accounts, see [Service accounts](./service-accounts.md).

:::info Agent accounts vs the authentik Agent
Agent accounts are separate from the authentik Agent. The authentik Agent is a deployable component on Windows, Linux, and macOS devices for device integration with authentik. For more information, see [authentik Agent](../../../endpoint-devices/authentik-agent/index.mdx).
:::

## About agent accounts

An agent account is a non-human identity with:

- A generated username.
- A parent user.
- No usable password.
- An API token for Bearer authentication.
- A configurable policy inheritance behavior.
- Audit events that identify the parent user.

For authorization, authentik treats an agent like any other service account. You can grant them access through groups, roles, object permissions, application bindings, and policies.

## Permissions for managing agent accounts

The following permissions control a user's ability to create, view, change, and delete agent accounts:

- Can add Agent
- Can change Agent
- Can delete Agent
- Can view Agent
- Add an agent user (self-service)

When an agent is created, authentik automatically grants the parent user permission to view, change, and delete it.

Users who are not the parent can manage an agent only if they have the required object or global permissions.

:::warning Self-service permission
The add agent permission disables access to self-service, even if the user also has the self-service permission.
:::

## Create an agent account

You can create an agent account in two ways:

- [**User interface (Self-service)**](#create-an-agent-via-the-user-interface-self-service): Internal users with the required permissions can create their own agents in the User interface.
- [**authentik API**](#create-an-agent-via-the-authentik-api): Agents can be created programmatically via the authentik API.

### Create an agent via the user interface (self-service)

An authenticated user with the required roles can create an agent for themselves. Self-service agents have the following properties:

- The parent is always the authenticated user. A user cannot create an agent for another user through self-service creation.
- The agent always expires.
- The agent uses the default token duration of the authentik deployment.
- The agent always uses [`NONE` policy behavior](#policy-behavior) and copies no access from its parent.
- Request values for `expiring`, `expires`, and `policy_behavior` are ignored.

To create an agent:

1. Log in to authentik as a user with the required roles and open the user interface.
2. Open the **Agents** page and click **Create Agent**.
3. Optionally enter a **Label** for the agent and click **Create**.
4. The token for the agent is displayed. Securely store this token because it will not be displayed again.

This token can now be used to authenticate as the agent.

### Create an agent via the authentik API

Create an agent account with the authentik API:

```http
POST /api/v3/agents/agents/
```

The request body can contain the following fields:

| Field             | Required | Description                                                                                                            |
| ----------------- | -------- | ---------------------------------------------------------------------------------------------------------------------- |
| `parent`          | No       | The ID of the user for whom the agent acts. If omitted, the authenticated user is used.                                |
| `label`           | No       | A display name for the agent.                                                                                          |
| `expiring`        | No       | Whether the agent account expires. The default is `false` for administrator-provisioned agents.                        |
| `expires`         | No       | The expiration date and time for the agent account.                                                                    |
| `policy_behavior` | No       | How the agent inherits policy access from its parent. The default is `MIRROR`. See [Policy behavior](#policy-behavior) |

The `parent` field is optional when an authenticated user creates an agent for themselves. An administrator or a user with the `Can add Agent` role can specify another user as the parent.

Here is an example of an API request to create an agent account:

```bash
curl \
  --request POST \
  --header "Authorization: Bearer <administrator-token>" \
  --header "Content-Type: application/json" \
  --data '{
    "parent": 123,
    "label": "automation-agent",
    "expiring": true,
    "expires": "2027-01-01T00:00:00Z",
    "policy_behavior": "MIRROR"
  }' \
  https://authentik.company/api/v3/agents/agents/
```

The response contains the agent and the generated API token:

```json
{
    "agent": {
        "pk": 456,
        "username": "<parent-username>-agent-<generated-id>",
        "name": "automation-agent",
        "expiring": true,
        "expires": "2027-01-01T00:00:00Z",
        "parent": {
            "pk": 123
        },
        "policy_behavior": "MIRROR",
        "token_identifier": "<parent-username>-agent-<generated-id>"
    },
    "token": "<agent-token>"
}
```

:::warning Token value
The token value is returned when the agent is created. Store it securely before closing or discarding the response. The `token_identifier` identifies the token but cannot be used to authenticate.
:::

## Policy behavior

An agent can inherit policy access from its parent in one of three ways. You select the policy behavior when you create the agent; you cannot change it afterwards. For [self-service agents](#create-an-agent-via-the-user-interface-self-service), policy behavior is not configurable and defaults to `NONE`.

### Mirror the parent (`MIRROR`)

`MIRROR` evaluates the agent as its parent user.

- The agent follows the parent's current policy access.

Use `MIRROR` when an agent must follow the parent's current access.

### Copy the parent's policy bindings (`COPY`)

`COPY` copies the parent's policy bindings when the agent is created. Only bindings referencing the parent as a user are copied. Access the parent derives from group membership is not copied.

- The agent receives a snapshot of the parent's policy bindings.
- Later changes to the parent's policy bindings do not update the copied bindings.
- The copied bindings are assigned to the agent independently of the parent.

Use `COPY` when an agent needs a stable snapshot of the parent's policy bindings.

### Do not inherit policies (`NONE`)

`NONE` does not copy or mirror the parent's policy bindings.

- The agent is evaluated independently of its parent for policy bindings.
- Grant access to the agent through its own groups, roles, object permissions, application bindings, or policies.

Use `NONE` when an agent must have independent policy access.

:::tip
Use `MIRROR` unless you specifically need a policy snapshot or independent policy access. `COPY` does not automatically update subsequent changes to the parent user's policy bindings.
:::

## Grant access for an agent

Agent accounts start with no special access beyond their ability to authenticate. Grant access through the same mechanisms used for other service accounts and users:

- Add the agent to a group.
- Add the agent to a role.
- Grant object permissions directly to the agent.
- Configure application bindings.
- Configure policies.
- Use the agent's policy behavior to inherit access from its parent.

For more information, see [Manage permissions](../../access-control/manage_permissions.md).

## Authenticate with an agent token

Use the generated token as a Bearer token when calling the authentik API:

```http
Authorization: Bearer <agent-token>
```

For example:

```bash
curl \
  --header "Authorization: Bearer <agent-token>" \
  https://authentik.company/api/v3/core/users/me/
```

The request is authenticated as the agent. authentik authorizes the request using the agent's assigned permissions and any endpoint-specific or object-level access checks. The agent’s policy behavior does not apply to direct API endpoint access.

:::warning Handling agent tokens
Treat an agent token as a credential. Store it in a secret manager or another protected secret store. Do not commit it to source control or include it in logs.
:::

## Manage agent tokens

An API token is created automatically for every agent. The token has the following properties:

- It is associated with the agent user.
- It always expires.
- It uses the default token duration.
- Its identifier is the generated agent username.

The agent's expiration and the token's expiration are separate:

- A self-service agent always expires using the default token duration.
- An administrator-provisioned agent can be configured to expire or not expire.
- The API token created for an agent always expires using the default token duration.
- On expiry the token is deleted and not rotated unlike the other service account tokens.

Agent tokens are managed in the same token system as other authentik tokens. See [Service accounts](./service-accounts.md) for general token-management information.

Users with the `Can view token` permission can retrieve their agents' tokens from the **Agents** page by clicking the **Copy token** icon next to the agent.

## Agent API operations

The agent API supports the following operations:

| Operation                 | Method   | Endpoint                      |
| ------------------------- | -------- | ----------------------------- |
| List agents               | `GET`    | `/api/v3/agents/agents/`      |
| Create an agent           | `POST`   | `/api/v3/agents/agents/`      |
| Retrieve an agent         | `GET`    | `/api/v3/agents/agents/<id>/` |
| Update an agent           | `PUT`    | `/api/v3/agents/agents/<id>/` |
| Partially update an agent | `PATCH`  | `/api/v3/agents/agents/<id>/` |
| Delete an agent           | `DELETE` | `/api/v3/agents/agents/<id>/` |

See the [API reference](https://api.goauthentik.io/) for the complete request and response schemas.

### Update an agent

You can update the agent's standard user fields, such as its name, email address, attributes, and active status.

The following fields are read-only after creation so a PUT must omit them:

- `parent`
- `policy_behavior`
- `token_identifier`

### Delete an agent

Deleting an agent deletes its associated API token. Requests authenticated with that token fail after the agent is deleted.

Deleting the parent user does not delete the agent. The agent remains as a parentless service account.

## Audit events

Actions performed by an agent are attributed to the agent's parent user in audit events.

Agent audit data identifies:

- The actor as an agent.
- The user on whose behalf the agent acted.

Service accounts without a parent user are attributed to themselves.

Review [Events](../../../sys-mgmt/events/index.md) when investigating agent activity or validating that an integration has the expected access.

## Troubleshooting

### Self-service creation is denied

Check the following:

- The request creates the agent for the authenticated user.
- The authenticated user is not attempting to set another user as the parent.
- The add agent permission disables access to self-service, even if the user also has the self-service permission.

### An agent cannot access an application

Check the following:

- The agent's `policy_behavior`.
- The parent's current policy access when using `MIRROR`.
- The copied policy bindings when using `COPY`.
- The agent's own groups, roles, permissions, application bindings, and policies when using `NONE`.
- The agent's active status and expiration.
- The token's active status and expiration.
- The request's `Authorization` header.

### An agent token no longer works

Check the following:

- The token has not expired.
- The token has not been revoked or deleted.
- The agent has not expired or been disabled.
- The token value is complete.
- The integration sends the token as a Bearer token.
