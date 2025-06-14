# Meta models

Since blueprints have a pretty strict mapping of each entry mapping to an instance of a model in the database, _meta models_ exist to trigger other actions within authentik that don't directly map to a model.

### `authentik_blueprints.metaapplyblueprint`

This meta model can be used to apply another blueprint instance within a blueprint instance. This allows for dependency management and ensuring related objects are created.

See [examples](https://github.com/search?q=repo%3Agoauthentik%2Fauthentik+path%3A%2F%5Eblueprints%5C%2F%2F+metaapplyblueprint&type=code) in the default blueprints for more information.

#### Attributes

- `identifiers`: Key-value attributes used to match the blueprint instance

    Example:

    ```yaml
    attrs:
        identifiers:
            name: Default - Password change flow
    ```

- `required`: (Default: `true`) Configure if the blueprint instance must exist

    If this is set to `true` and no blueprint instance matches the query above, an error will be thrown. Otherwise, execution will continue without applying anything extra.
