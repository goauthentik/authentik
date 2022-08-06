---
title: File structure
---

Blueprints are YAML files, which can use some additional tags to ease blueprint creation.

## Additional Tags

#### `!KeyOf`

Example: `policy: !KeyOf my-policy-id`

Resolves to the primary key of the model instance defined by id _my-policy-id_.

If no matching entry can be found, an error is raised and the blueprint is invalid.

#### `!Find`

Example: `configure_flow: !Find [authentik_flows.flow, [slug, default-password-change]]`

Looks up any model and resolves to the the matches' primary key.
First argument is the model to be queried, remaining arguments are expected to be pairs of key=value pairs to query for.

#### `!Context`

Example: `configure_flow: !Context foo`

Find values from the context. Can optionally be called with a default like `!Context [foo, default-value]`.

## Structure

```yaml
# The version of this blueprint, currently 1
version: 1
# Optional block of metadata, name is required if metadata is set
metadata:
    # Arbitrary key=value store, special labels are listed below
    labels:
        foo: bar
    name: example-blueprint
# Optional default context, instance context is merged over this.
context:
    foo: bar
# List of entries (required)
entries:
    - # Model in app.model notation, possibilities are listed in the schema (required)
      model: authentik_flows.flow
      # Key:value filters to uniquely identify this object (required)
      identifiers:
          slug: initial-setup
      # Optional ID for use with !KeyOf
      id: flow
      # Attributes to set on the object. Only explicitly required settings should be stated
      # as these values will override existing attributes
      attrs:
          denied_action: message_continue
          designation: stage_configuration
          name: default-oobe-setup
          title: Welcome to authentik!
```

## Special Labels

#### `blueprints.goauthentik.io/system`:

Used by authentik's packaged blueprints to keep globals up-to-date. Should only be removed in special cases.

#### `blueprints.goauthentik.io/example`:

Blueprints with this label are not automatically imported. They are still available when creating a new instance.
