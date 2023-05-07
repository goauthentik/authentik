# File structure

Blueprints are YAML files, which can use some additional tags to ease blueprint creation.

## Structure

```yaml
# yaml-language-server: $schema=https://goauthentik.io/blueprints/schema.json
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
      # The state this object should be in (optional, can be "present", "created" or "absent")
      # Present will keep the object in sync with its definition here, created will only ensure
      # the object is created (and create it with the values given here), and "absent" will
      # delete the object
      state: present
      # An optional list of boolean-like conditions. If all conditions match (or
      # no condiitons are provided) the entry will be evaluated and acted upon
      # as normal. Otherwise, the entry is skipped as if not defined at all.
      # Each condition will be evaluated in Python to its boolean representation
      # bool(<condition>). Furthermore, complex conditions can be built using
      # a special !Condition tag. See the documentattion for custom tags for more
      # information.
      conditions:
          - true
          - text
          - 2
          - !Condition [AND, ...] # See custom tags section
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

#### `blueprints.goauthentik.io/instantiate`:

Configure if this blueprint should automatically be instantiated (defaults to `"true"`). When set to `"false"`, blueprints are listed and available to be instantiated via API/Browser.

#### `blueprints.goauthentik.io/description`:

Optionally set a description, which can be seen in the web interface.
