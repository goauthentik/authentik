---
title: Blueprints
---

:::info
Requires authentik 2022.8
:::

Blueprints offer a new way to template, automate and distribute authentik configuration. Blueprints can be used to automatically configure instances, manage config as code without any external tools, and to distribute application configs.

## Types

Blueprints are yaml files, whose format is described further in [File structure](./v1/structure). Blueprints can be applied in one of two ways:

-   As a Blueprint instance, which is a YAML file mounted into the authentik (worker) container. This file is read and applied regularly (every 60 minutes). Multiple instances can be created for a single blueprint file, and instances can be given context key:value attributes to configure the blueprint.

    :::info
    Starting with authentik 2022.12.1, authentik watches for file modification/creation events in the blueprint directory and will automatically trigger a discovery when a new blueprint file is created, and trigger a blueprint apply when a file is modified.
    :::

-   As a Flow import, which is a YAML file uploaded via the Browser/API. This file is validated and applied directly after being uploaded, but is not further monitored/applied.

Starting with authentik 2022.8, blueprints are used to manage authentik default flows and other system objects. These blueprints can be disabled/replaced with custom blueprints in certain circumstances.

## Storage - File

The authentik container by default looks for blueprints in `/blueprints`. Underneath this directory, there are a couple default subdirectories:

-   `/blueprints/default`: Default blueprints for default flows, tenants, etc
-   `/blueprints/example`: Example blueprints for common configurations and flows
-   `/blueprints/system`: System blueprints for authentik managed Property mappings, etc

Any additional `.yaml` file in `/blueprints` will be discovered and automatically instantiated, depending on their labels.

To disable existing blueprints, an empty file can be mounted over the existing blueprint.

File-based blueprints are automatically removed once they become unavailable, however none of the objects created by those blueprints afre affected by this.

## Storage - OCI

Blueprints can also be stored in remote [OCI](https://opencontainers.org/) compliant registries. This includes GitHub Container Registry, Docker hub and many other registries.

To download a blueprint via OCI, set the path to `oci://ghcr.io/<username>/<package-name>:<ref>`. This will fetch the blueprint from an OCI package hosted on GHCR.

To fetch blueprints from a private registry with authentication, credentials can be embedded into the URL.

Blueprints are re-fetched each execution, so when using changing tags, blueprints will automatically be updated.

To push a blueprint to an OCI-compatible registry, [ORAS](https://oras.land/) can be used with this command

```
oras push ghcr.io/<username>/blueprint/<blueprint name>:latest <yaml file>:application/vnd.goauthentik.blueprint.v1+yaml
```

## Storage - Internal

:::info
Requires authentik 2023.1
:::

Blueprints can be stored in authentik's database, which allows blueprints to be managed via external configuration management tools like Terraform.

Modifying the contents of a blueprint will trigger its reconciliation. Blueprints are validated on submission to prevent invalid blueprints from being saved.
