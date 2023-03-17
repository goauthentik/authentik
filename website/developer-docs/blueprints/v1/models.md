# Models

Some models behave differently and allow for access to different API fields when created via blueprint.

### `authentik_core.token`

:::info
Requires authentik 2023.4
:::

Via the standard API, a token's key cannot be changed, it can only be rotated. This is to ensure a high entropy in it's key, and to prevent insecure data from being used. However, when provisioning tokens via a blueprint, it may be required to set a token to an existing value.

With blueprints, the field `key` can be set, to set the token's key to any value.

For example:

```yaml
# [...]
- model: authentik_core.token
  state: present
  identifiers:
      identifier: my-token
  attrs:
      key: this-should-be-a-long-value
      user: !KeyOf my-user
      intent: api
```
