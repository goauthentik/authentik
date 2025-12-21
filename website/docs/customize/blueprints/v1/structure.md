# File structure

Blueprints are YAML files, which can use some additional tags to ease blueprint creation.

## Schema

The blueprint schema is available under `https://goauthentik.io/blueprints/schema.json`. It is also possible to target a specific version's blueprint schema by using `https://version-2023-4.goauthentik.io/blueprints/schema.json`.

To use the schema with Visual Studio code and the YAML extension, add this comment at the top of your blueprint files:

```yaml
# yaml-language-server: $schema=https://goauthentik.io/blueprints/schema.json
```

## Example

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
      # The state this object should be in (optional, can be "present", "created", "must_created", or "absent")
      # - present (default): Creates the object if it doesn't exist, or updates the fields
      #   specified in attrs if it does exist. This will overwrite any manual changes to those
      #   fields, but fields not in attrs are left unchanged.
      # - created: Creates the object if it doesn't exist, but never updates it afterward.
      #   Manual changes are preserved.
      # - must_created: Creates the object only if it doesn't exist. If the object already exists,
      #   the blueprint will fail with a validation error.
      # - absent: Deletes the object if it exists. This uses Django's .delete() which may
      #   cascade to related objects (e.g., deleting a Flow will delete its FlowStageBindings).
      state: present
      # An optional list of boolean-like conditions. If all conditions match (or
      # no conditions are provided) the entry will be evaluated and acted upon
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
      # On creation: identifiers are merged with attrs to create the object
      # On lookup: identifiers are used to find existing objects (using OR logic - see below)
      # On update: only attrs are applied (if state is present)
      #
      # Multiple identifiers create an OR query: an object matches if ANY identifier matches.
      # Example: identifiers with both slug and pk will match if either the slug OR pk matches.
      #
      # Dictionary values use Django's __contains query for JSON field matching:
      # identifiers:
      #     attributes: {foo: bar}  # Matches if attributes JSON contains {"foo": "bar"}
      identifiers:
          slug: initial-setup
      # Optional ID for use with !KeyOf
      id: flow
      # Attributes to set on the object. Only explicitly required settings should be stated
      # as these values will override existing attributes.
      # Note: When creating objects, both identifiers and attrs are merged together.
      # On updates (state: present), only fields specified in attrs are modified - other
      # fields (like auto-generated client_id/client_secret) are left unchanged.
      attrs:
          denied_action: message_continue
          designation: stage_configuration
          name: default-oobe-setup
          title: Welcome to authentik!
      # Optionally set object-level permissions on the object
      # Requires authentik 2024.8
      permissions:
          - permission: inspect_flow
            user: !Find [authentik_core.user, [username, akadmin]]
```

## Special Labels

#### `blueprints.goauthentik.io/system`:

Used by authentik's packaged blueprints to keep globals up-to-date. Should only be removed in special cases.

#### `blueprints.goauthentik.io/instantiate`:

Configure if this blueprint should automatically be instantiated (defaults to `"true"`). When set to `"false"`, blueprints are listed and available to be instantiated via API/Browser.

#### `blueprints.goauthentik.io/description`:

Optionally set a description, which can be seen in the web interface.
