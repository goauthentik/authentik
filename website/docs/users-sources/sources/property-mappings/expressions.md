---
title: Sources expression property mappings
---

The property mapping should return a value that is expected by the source. Returning `None` is always accepted and skips the mapping that returned `None`.

## Variables

- Arbitrary arguments given by the source (this is documented by the source).
- `properties`: A Python dictionary containing the result of the previously run property mappings, plus the initial data computed by the source.
- `request`: The current request. This can be `None` if there is no contextual request. See the [Django documentation](https://docs.djangoproject.com/en/3.0/ref/request-response/#httprequest-objects).

import Objects from "../../../expressions/reference/\_objects.md";

<Objects />

## Available functions

import Functions from "../../../expressions/reference/\_functions.mdx";

<Functions />
