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

### `authentik_core.application`

:::info
Requires authentik 2023.5
:::

Application icons can be directly set to URLs with the `icon` field.

For example:

```yaml
# [...]
- model: authentik_core.application
  identifiers:
      slug: my-app
  attrs:
      name: My App
      icon: https://goauthentik.io/img/icon.png
```

### `authentik_sources_oauth.oauthsource`, `authentik_sources_saml.samlsource`, `authentik_sources_plex.plexsource`

:::info
Requires authentik 2023.5
:::

Source icons can be directly set to URLs with the `icon` field.

For example:

```yaml
# [...]
- model: authentik_sources_oauth.oauthsource
  identifiers:
      slug: my-source
  attrs:
      name: My source
      icon: https://goauthentik.io/img/icon.png
```

### `authentik_flows.flow`

:::info
Requires authentik 2023.5
:::

Flow backgrounds can be directly set to URLs with the `background` field.

For example:

```yaml
# [...]
- model: authentik_flows.flow
  identifiers:
      slug: my-flow
  attrs:
      name: my-flow
      title: My flow
      designation: authentication
      background: https://goauthentik.io/img/icon.png
```
