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
-   As a Flow import, which is a YAML file uploaded via the Browser/API. This file is validated and applied directly after being uploaded, but is not further monitored/applied.

Starting with authentik 2022.8, blueprints are used to manage authentik default flows and other system objects. These blueprints can be disabled/replaced with custom blueprints in certain circumstances.

## Usage

The authentik container by default looks for blueprints in `/blueprints`. Underneath this directory, there are a couple default subdirectories:

-   `/blueprints/default`: Default blueprints for default flows, tenants, etc
-   `/blueprints/example`: Example blueprints for common configurations and flows
-   `/blueprints/system`: System blueprints for authentik managed Property mappings, etc

Any additional `.yaml` file in `/blueprints` will be discovered and automatically instantiated, depending on their labels.

To disable existing blueprints, an empty file can be mounted over the existing blueprint.
