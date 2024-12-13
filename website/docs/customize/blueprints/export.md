---
title: Export
---

## Global export

To migrate existing configurations to blueprints, run `ak export_blueprint` within any authentik Worker container. This will output a blueprint for most currently created objects. Some objects will not be exported as they might have dependencies on other things.

Exported blueprints don't use any of the YAML Tags, they just contain a list of entries as they are in the database.

Note that fields which are write-only (for example, OAuth Provider's Secret Key) will not be added to the blueprint, as the serialisation logic from the API is used for blueprints.

Additionally, default values will be skipped and not added to the blueprint.

## Flow exports

Instead of exporting everything from a single instance, there's also the option to export a single flow with it's attached stages, policies and other objects.

This export can be triggered via the API or the Web UI by clicking the download button in the flow list.

## Cleaning up

Exports from either method will contain a (potentially) long list of objects, all with hardcoded primary keys and no ability for templating/instantiation. This is because currently, authentik does not check which primary keys are used where. It is assumed that for most exports, there'll be some manual changes done regardless, to filter out unwanted objects, adjust properties, etc.
