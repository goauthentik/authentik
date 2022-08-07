# YAML Tags

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

#### `!Format`

Example: `name: !Format [my-policy-%s, !Context instance_name]`

Format a string using python's % formatting. First argument is the format string, any remaining arguments are used for formatting.
