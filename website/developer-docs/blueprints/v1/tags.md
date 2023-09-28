# YAML Tags

#### `!KeyOf`

Example: `policy: !KeyOf my-policy-id`

Resolves to the primary key of the model instance defined by id _my-policy-id_.

If no matching entry can be found, an error is raised and the blueprint is invalid.

#### `!Env`

Example: `password: !Env my_env_var`

Returns the value of the given environment variable. Can be used as a scalar with `!Env my_env_var, default` to return a default value.

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

```yaml
# Short form
# !If [<condition>]
required: !If [true]
```

```yaml
# Longer form
# !If [<condition>, <when true>, <when false>]
required: !If [true, true, false]
```

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

Similar to a one-line if, the first argument is the condition, which can be any valid yaml or custom tag. It will be evaluated as boolean in python. However, keep in mind that dictionaries and lists will always evaluate to `true`, unless they are empty.

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

#### `!Enumerate`, `!Index` and `!Value`

These tags collectively make it possible to iterate over objects which support iteration. Any iterable Python object is supported. Such objects are sequences (`[]`), mappings (`{}`) and even strings.

1. `!Enumerate` tag:

This tag takes 3 arguments:

```
!Enumerate [<iterable>, <output_object_type>, <single_item_yaml>]
```

-   **iterable**: Any Python iterable or custom tag that resolves to such iterable
-   **output_object_type**: `SEQ` or `MAP`. Controls whether the returned YAML will be a mapping or a sequence.
-   **single_item_yaml**: The YAML to use to create a single entry in the output object

2. `!Index` tag:

:::info
This tag is only valid inside an `!Enumerate` tag
:::

This tag takes 1 argument:

```
!Index <depth>
```

-   **depth**: Must be >= 0. A depth of 0 refers to the `!Enumerate` tag this tag is located in. A depth of 1 refers to one `!Enumerate` tag above that (to be used when multiple `!Enumerate` tags are nested inside each other).

Accesses the `!Enumerate` tag's iterable and resolves to the index of the item currently being iterated (in case `!Enumerate` is iterating over a sequence), or the mapping key (in case `!Enumerate` is iterating over a mapping).

For example, given a sequence like this - `["a", "b", "c"]`, this tag will resolve to `0` on the first `!Enumerate` tag iteration, `1` on the second and so on. However, if given a mapping like this - `{"key1": "value1", "key2": "value2", "key3": "value3"}`, it will first resolve to `key1`, then to `key2` and so on.

3. `!Value` tag:

:::info
This tag is only valid inside an `!Enumerate` tag
:::

This tag takes 1 argument:

```
!Value <depth>
```

-   **depth**: Must be >= 0. A depth of 0 refers to the `!Enumerate` tag this tag is located in. A depth of 1 refers to one `!Enumerate` tag above that (to be used when multiple `!Enumerate` tags are nested inside each other).

Accesses the `!Enumerate` tag's iterable and resolves to the value of the item currently being iterated.

For example, given a sequence like this - `["a", "b", "c"]`, this tag will resolve to `a` on the first `!Enumerate` tag iteration, `b` on the second and so on. If given a mapping like this - `{"key1": "value1", "key2": "value2", "key3": "value3"}`, it will first resolve to `value1`, then to `value2` and so on.

Minimal examples:

```
configuration_stages: !Enumerate [
    !Context map_of_totp_stage_names_and_types,
    SEQ, # Output a sequence
    !Find [!Format ["authentik_stages_authenticator_%s.authenticator%sstage", !Index 0, !Index 0], [name, !Value 0]] # The value of each item in the sequence
]
```

The above example will resolve to something like this:

```
configuration_stages:
- !Find [authentik_stages_authenticator_<stage_type_1>.authenticator<stage_type_1>stage, [name, <stage_name_1>]]
- !Find [authentik_stages_authenticator_<stage_type_2>.authenticator<stage_type_2>stage, [name, <stage_name_2>]]
```

Similarly, a mapping can be generated like so:

```
example: !Enumerate [
    !Context list_of_totp_stage_names,
    MAP, # Output a map
    [
        !Index 0, # The key to assign to each entry
        !Value 0, # The value to assign to each entry
    ]
]
```

The above example will resolve to something like this:

```
example:
  0: <stage_name_1>
  1: <stage_name_2>
```

Full example:

:::caution
Note that an `!Enumeration` tag's iterable can never be an `!Item` or `!Value` tag with a depth of `0`. Minimum depth allowed is `1`. This is because a depth of `0` refers to the `!Enumeration` tag the `!Item` or `!Value` tag is in, and an `!Enumeration` tag cannot iterate over itself.
:::

```
example: !Enumerate [
    !Context sequence, # ["foo", "bar"]
    MAP, # Output a map
    [
        !Index 0, # Use the indexes of the items in the sequence as keys
        !Enumerate [ # Nested enumeration
            # Iterate over each item of the parent enumerate tag.
            # Notice depth is 1, not 0, since we are inside the nested enumeration tag!
            !Value 1,
            SEQ, # Output a sequence
            !Format ["%s: (index: %d, letter: %s)", !Value 1, !Index 0, !Value 0]
        ]
    ]
]
```

The above example will resolve to something like this:

```
'0':
- 'foo: (index: 0, letter: f)'
- 'foo: (index: 1, letter: o)'
- 'foo: (index: 2, letter: o)'
'1':
- 'bar: (index: 0, letter: b)'
- 'bar: (index: 1, letter: a)'
- 'bar: (index: 2, letter: r)'
```
