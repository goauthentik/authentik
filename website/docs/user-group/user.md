---
title: User
---

## Path

:::info
Requires authentik 2022.7
:::

Paths can be used to organize users into folders depending on which source created them or organizational structure. Paths may not start or end with a slash, but they can contain any other character as path segments. The paths are currently purely used for organization, it does not affect their permissions, group memberships, or anything else.

## Attributes

### `goauthentik.io/user/can-change-username`

Optional flag, when set to false prevents the user from changing their own username.

### `goauthentik.io/user/can-change-name`

Optional flag, when set to false prevents the user from changing their own name.

### `goauthentik.io/user/can-change-email`

Optional flag, when set to false prevents the user from changing their own email address.

### `goauthentik.io/user/token-expires`:

Optional flag, when set to false, Tokens created by the user will not expire.

Only applies when the token creation is triggered by the user with this attribute set. Additionally, the flag does not apply to superusers.

### `goauthentik.io/user/debug`:

See [Troubleshooting access problems](../troubleshooting/access.md), when set, the user gets a more detailed explanation of access decisions.

### `additionalHeaders`:

:::info
This field is only used by the Proxy Provider.
:::

Some applications can be configured to create new users using header information forwarded from authentik. You can forward additional header information by adding each header
underneath `additionalHeaders`:

#### Example:

```
additionalHeaders:
  REMOTE-USER: joe.smith
  REMOTE-EMAIL: joe@jsmith.com
  REMOTE-NAME: Joseph
```

These headers will now be passed to the application when the user logs in. Most applications will need to be configured to accept these headers. Some examples of applications that can accept additional headers from an authentik Proxy Provider are [Grafana](https://grafana.com/docs/grafana/latest/auth/auth-proxy/) and [Tandoor Recipes](https://docs.tandoor.dev/features/authentication/).

## Object attributes

The User object has the following attributes:

-   `username`: User's username.
-   `email` User's email.
-   `uid` User's unique ID
-   `name` User's display name.
-   `is_staff` Boolean field if user is staff.
-   `is_active` Boolean field if user is active.
-   `date_joined` Date user joined/was created.
-   `password_change_date` Date password was last changed.
-   `attributes` Dynamic attributes, see above
-   `group_attributes()` Merged attributes of all groups the user is member of and the user's own attributes.
-   `ak_groups` This is a queryset of all the user's groups.

    You can do additional filtering like

    ```python
    user.ak_groups.filter(name__startswith='test')
    ```

    see [here](https://docs.djangoproject.com/en/3.1/ref/models/querysets/#id4)

    To get the name of all groups, you can do

    ```python
    [group.name for group in user.ak_groups.all()]
    ```

## Examples

List all the User's group names:

```python
for group in user.ak_groups.all():
    yield group.name
```
