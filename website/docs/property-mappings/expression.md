---
title: Property Mapping Expressions
---

The property mapping should return a value that is expected by the Provider/Source. Supported types are documented in the individual Provider/Source. Returning `None` is always accepted and would simply skip the mapping for which `None` was returned.

:::note
These variables are available in addition to the common variables/functions defined in [**Expressions**](../expressions/index.md)
:::

### Context Variables

- `user`: The current user. This may be `None` if there is no contextual user. ([ref](../expressions/reference/user-object.md))
- `request`: The current request. This may be `None` if there is no contextual request. ([ref](https://docs.djangoproject.com/en/3.0/ref/request-response/#httprequest-objects))
- Other arbitrary arguments given by the provider, this is documented on the Provider/Source.
