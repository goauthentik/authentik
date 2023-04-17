---
title: Flow Context
---

Each flow execution has an independent context. This context can hold arbitrary data, which can be used and transformed by stages and policies.

## Managing data in a flow context
You create and manage the data for a context by configuring policies, stages, and bindings. As you plan your flow, and setup the requird stages, etc. you are creating the context data for that flow.

For example, in the Identification Stage (part of the default login flow), you can define whether users will be prompted to enter an email address, a username, or both. All such information about the flow's configuration makes up the context.

Any data can be stored in the flow context, however there are some reserved keys in the context dictionary that are used by authentik stages.

## Context dictionary and reserved keywords

This section describes the commmon data objects that are used in authentik, and provides a list of reserved keys that should not be used except by authentik internally.

### Common objects

#### `pending_user` (User object)

`pending_user` is used by multiple stages. In the context of most flow executions, it holds the user that is executing the flow. This value is not set automatically, it is set via the [Identification stage](../stages/identification/).

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

Stores the final redirect that the user's browser will be sent to after the flow is finished executing successfully. This is set when an un-authenticated user attempts to access a secured application, and when a user authenticates/enrolls with an external source.

#### `application` (Application object)

When an unauthenticated user attempts to access a secured resource, they are redirected to an authentication flow. The application they attempted to access will be stored in this key.

#### `source` (Source object)

When a user authenticates/enrolls via an external source, this will be set to the source they are using.

### Scenario-specific

#### `is_sso` (boolean)

Set to `True` when the flow is executed from an "SSO" context. For example, this is set when a flow is used during the authentication or enrollment via an external source, and if a flow is executed to authorize access to an application.

### Stage-specific

#### Consent stage

##### `consent_header` (string)

The title of the consent prompt shown. Set automatically when the consent stage is used with a OAuth2, Proxy or SAML provider.

##### `consent_permissions` (List of PermissionDict)

An optional list of all permissions that will be given to the application by granting consent. Not supported with SAML. When used with an OAuth2 or Proxy provider, this will be set based on the configured scopes.

#### Autosubmit stage

The autosubmit stage is an internal stage type that is not configurable via the API/Web interface. It is used in certain situations, where a POST request has to be sent from the browser, such as with SAML POST bindings. This works by using an HTML form that is submitted automatically.

##### `title` (string)

Optional title of the form shown to the user. Automatically set when this stage is used by the backend.

##### `url` (string)

URL that the form will be submitted to.

##### `attrs` (dict)

Key-value pairs of the data that is included in the form and will be submitted to `url`.

#### User write stage

##### `groups` (List of Group objects)

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

##### `auth_method_args` (dict)

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
