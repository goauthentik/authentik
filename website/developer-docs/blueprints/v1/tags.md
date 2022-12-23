# YAML Tags

#### `!KeyOf`

Example: `policy: !KeyOf my-policy-id`

Resolves to the primary key of the model instance defined by id _my-policy-id_.

If no matching entry can be found, an error is raised and the blueprint is invalid.

#### `!Find`

Examples:

`configure_flow: !Find [authentik_flows.flow, [slug, default-password-change]]`

```
configure_flow: !Find [
  authentik_flows.flow,
  [
    !Context property_name,
    !Context property_value
  ]
]
```

Looks up any model and resolves to the the matches' primary key.
First argument is the model to be queried, remaining arguments are expected to be pairs of key=value pairs to query for.

#### `!Context`

Example: `configure_flow: !Context foo`

Find values from the context. Can optionally be called with a default like `!Context [foo, default-value]`.

#### `!Format`

Example: `name: !Format [my-policy-%s, !Context instance_name]`

Format a string using python's % formatting. First argument is the format string, any remaining arguments are used for formatting.

#### `!If`

Minimal example:

`required: !If [true, true, false] # !If [<condition>, <when true>, <when false>`

Full example:

```
attributes: !If [
    !Condition [...], # Or any valid YAML or custom tag. Evaluated as boolean in Python
    { # When condition evaluates to true
        dictionary:
        {
            with:
            {
                keys: "and_values"
            },
            and_nested_custom_tags: !Format ["foo-%s", !Context foo]
        }
    },
    [ # When condition evaluates to false
        list,
        with,
        items,
        !Format ["foo-%s", !Context foo]
    ]
]
```

Conditionally add YAML to a blueprint.

Similar to a one-line if, the first argument is the condition, which can be any valid yaml or custom tag. It will be evaluted as boolean in python. However, keep in mind that dictionaries and lists will always evaluate to `true`, unless they are empty.

The second argument is used when the condition is `true`, and the third - when `false`. The YAML inside both arguments will be fully resolved, thus it is possible to use custom YAML tags and even nest them inside dictionaries and lists.

#### `!Condition`

Minimal example:

`required: !Condition [OR, true]`

Full example:

```
required: !Condition [
    AND, # Valid modes are: AND, NAND, OR, NOR, XOR, XNOR
    !Context instance_name,
    !Find [authentik_flows.flow, [slug, default-password-change],
    "My string",
    123
]
```

Converts one or more arguments to their boolean representations, then merges all representations together.
Requires at least one argument after the mode selection.

If only a single argument is provided, its boolean representation will be returned for all normal modes and its negated boolean representation will be returned for all negated modes.

Normally, it should be used to define complex conditions for use with an `!If` tag or for the `conditions` attribute of a blueprint entry (see [the blueprint file structure](./structure.md)). However, this is essentially just a boolean evaluator so it can be used everywhere a boolean representation is required.
