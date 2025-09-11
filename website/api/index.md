---
title: API Overview
sidebar_label: Overview
---

Our API reference documentation is generated from the [OpenAPI v3 schema](https://docs.goauthentik.io/schema.yml).

You can also access your installation's own, instance-specific API Browser. Starting with 2021.3.5, every authentik instance has a built-in API browser, which can be accessed at <code>https://<em>authentik.company</em>/api/v3/</code>.

To generate an API client you can use the OpenAPI v3 schema at <code>https://<em>authentik.company</em>/api/v3/schema/</code>.

## Making schema changes

Some backend changes might require new/different fields or remove other fields. To create a new schema after changing a Serializer, run `make gen-build`.

This will update the `schema.yml` file in the root of the repository.
