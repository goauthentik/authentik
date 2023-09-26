# Meta models

Since blueprints have a pretty strict mapping of each entry mapping to an instance of a model in the database, _meta models_ exist to trigger other actions within authentik that don't directly map to a model.

### `authentik_blueprints.metaapplyblueprint`

This meta model can be used to apply another blueprint instance within a blueprint instance. This allows for dependency management and ensuring related objects are created.

#### Attributes

-   `identifiers`: Key-value attributes used to match the blueprint instance

    Example:

    ```yaml
    attrs:
        identifiers:
            name: Default - Password change flow
    ```

-   `required`: (Default: `true`) Configure if the blueprint instance must exist

    If this is set to `true` and no blueprint instance matches the query above, an error will be thrown. Otherwise, execution will continue without applying anything extra.
