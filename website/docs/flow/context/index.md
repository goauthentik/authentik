---
title: Flow Context
---

Each flow execution has an independent _context_. This context holds all of the arbitrary data about that specific flow, data which can then be used and transformed by stages and policies.

## Managing data in a flow context

You create and manage the data for a context by configuring policies, stages, and bindings. As you plan your flow, and set up the required stages, etc. you are creating the context data for that flow.

For example, in the Identification Stage (part of the default login flow), you can define whether users will be prompted to enter an email address, a username, or both. All such information about the flow's configuration makes up the context.

Any data can be stored in the flow context, however there are some reserved keys in the context dictionary that are used by authentik stages.

## Context dictionary and reserved keys

This section describes the data (the context) that are used in authentik, and provides a list of keys, what they are used for and when they are set.

:::warning
Keys prefixed with `goauthentik.io` are used internally by authentik and are subject to change without notice, and should not be modified in policies in most cases.
:::

### Common keys

#### `pending_user` ([User object](../../user-group/user/user_ref.md#object-properties))

`pending_user` is used by multiple stages. In the context of most flow executions, it represents the data of the user that is executing the flow. This value is not set automatically, it is set via the [Identification stage](../stages/identification/).

Stages that require a user, such as the [Password stage](../stages/password/), the [Authenticator validation stage](../stages/authenticator_validate/) and others will use this value if it is set, and fallback to the request's users when possible.

#### `prompt_data` (Dictionary)

`prompt_data` is primarily used by the [Prompt stage](../stages/prompt/). The value of any field within a prompt stage is written to the `prompt_data` dictionary. For example, given a field with the _Field key_ `email` that was submitted with the value `foo@bar.baz` will result in the following context:

```json
{
    "prompt_data": {
        "email": "foo@bar.baz"
    }
}
```

This data can be modified with policies. The data is also used by stages like [User write](../stages/user_write.md), which takes data in `prompt_data` and writes it to `pending_user`.

#### `redirect` (string)

Stores the final redirect URL that the user's browser will be sent to after the flow is finished executing successfully. This is set when an un-authenticated user attempts to access a secured application, and when a user authenticates/enrolls with an external source.

#### `pending_user_identifier` (string)

If _Show matched user_ is disabled, this key will hold the user identifier entered by the user in the identification stage.

Stores the final redirect URL that the user's browser will be sent to after the flow is finished executing successfully. This is set when an un-authenticated user attempts to access a secured application, and when a user authenticates/enrolls with an external source.

#### `application` (Application object)

When an unauthenticated user attempts to access a secured resource, they are redirected to an authentication flow. The application they attempted to access will be stored in the key attached to this object. For example: `application.github`, with `application` being the key and `github` the value.

#### `source` (Source object)

When a user authenticates/enrolls via an external source, this will be set to the source they are using.

### Scenario-specific keys

#### `is_sso` (boolean)

Set to `True` when the flow is executed from an "SSO" context. For example, this is set when a flow is used during the authentication or enrollment via an external source, and if a flow is executed to authorize access to an application.

#### `is_restored` (Token object)

Set when a flow execution is continued from a token. This happens for example when an [Email stage](../stages/email/index.mdx) is used and the user clicks on the link within the email. The token object contains the key that was used to restore the flow execution.

### Stage-specific keys

#### Consent stage

##### `consent_header` (string)

The title of the consent prompt shown. Set automatically when the consent stage is used with a OAuth2, Proxy or SAML provider.

##### `consent_permissions` (List of PermissionDict)

An optional list of all permissions that will be given to the application by granting consent. Not supported with SAML. When used with an OAuth2 or Proxy provider, this will be set based on the configured scopes.

#### Autosubmit stage

The autosubmit stage is an internal stage type that is not configurable via the API/Web interface. It is used in certain situations, where a POST request is sent from the browser, such as with SAML POST bindings. This works by using an HTML form that is submitted automatically.

##### `title` (string)

Optional title of the form shown to the user. Automatically set when this stage is used by the backend.

##### `url` (string)

URL that the form will be submitted to.

##### `attrs` (dictionary)

Key-value pairs of the data that is included in the form and will be submitted to `url`.

#### Deny stage

##### `deny_message` (string)

:::info
Requires authentik 2023.10
:::

Optionally overwrite the deny message shown, has a higher priority than the message configured in the stage.

#### User write stage

##### `groups` (List of [Group objects](../../user-group/group.md))

See [Group](../../user-group/group.md). If set in the flow context, the `pending_user` will be added to all the groups in this list.

If set, this must be a list of group objects and not group names.

##### `user_path` (string)

Path the `pending_user` will be written to. If not set in the flow, falls back to the value set in the user_write stage, and otherwise to the `users` path.

#### Password stage

##### `user_backend` (string)

Set by the [Password stage](../stages/password/index.md) after successfully authenticating in the user. Contains a dot-notation to the authentication backend that was used to successfully authenticate the user.

##### `auth_method` (string)

Set by the [Password stage](../stages/password/index.md), the [Authenticator validation stage](../stages/authenticator_validate/index.md), the [OAuth2 Provider](../../providers/oauth2/index.md), and the API authentication depending on which method was used to authenticate.

Possible options:

-   `password` (Authenticated via the password in authentik's database)
-   `token` (Authenticated via API token)
-   `ldap` (Authenticated via LDAP bind from an LDAP source)
-   `auth_mfa` (Authentication via MFA device without password)
-   `auth_webauthn_pwl` (Passwordless authentication via WebAuthn)
-   `jwt` ([M2M](../../providers/oauth2/client_credentials.md) authentication via an existing JWT)

##### `auth_method_args` (dictionary)

Additional arguments used during the authentication. Value varies depending on `auth_method`.

Example:

```json
{
    // List of the MFA device objects used during authentication
    // applies for `auth_method` `auth_mfa`
    "mfa_devices": [],
    // MFA device used for passwordless authentication, applies to
    // `auth_method` `auth_webauthn_pwl`
    "device": null,
    // the token identifier when `auth_method` `token` was used
    "identifier": "",
    // JWT information when `auth_method` `jwt` was used
    "jwt": {},
    "source": null,
    "jwk_id": ""
}
```

#### Email stage

##### `email_sent` (boolean)

Boolean set to true after the email form the email stage has been sent.

##### `email` (string)

Optionally override the email address that the email will be sent to. If not set, defaults to the email of `pending_user`.

#### Identification stage

##### `pending_user_identifier` (string)

If _Show matched user_ is disabled, this key will be set to the user identifier entered by the user in the identification stage.
