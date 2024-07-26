---
title: Expressions
---

The property mapping should return a value that is expected by the source. Returning `None` is always accepted and would simply skip the mapping for which `None` was returned.

## Variables

-   Arbitrary arguments given by the Source, this is documented on the Source.
-   `properties`: A Python dictionary containing the result of the previously ran property mappings, plus the initial data computed by the Source.
-   `request`: The current request. This may be `None` if there is no contextual request. See ([Django documentation](https://docs.djangoproject.com/en/3.0/ref/request-response/#httprequest-objects))

import Objects from "../../expressions/\_objects.md";

<Objects />

## Available Functions

import Functions from "../../expressions/\_functions.md";

<Functions />
