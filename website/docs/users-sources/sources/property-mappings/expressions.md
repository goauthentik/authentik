---
title: Sources expression property mappings
---

The property mapping should return a value that is expected by the source. Returning `None` is always accepted and would simply skip the mapping for which `None` was returned.

## Variables

- Arbitrary arguments given by the source (this is documented by the source).
- `properties`: A Python dictionary containing the result of the previously run property mappings, plus the initial data computed by the source.
- `request`: The current request. This may be `None` if there is no contextual request. See ([Django documentation](https://docs.djangoproject.com/en/3.0/ref/request-response/#httprequest-objects))

import Objects from "../../../expressions/\_objects.md";

<Objects />

## Available Functions

import Functions from "../../../expressions/\_functions.mdx";

<Functions />
