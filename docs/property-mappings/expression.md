# Property Mapping Expressions

The property mapping should return a value that is expected by the Provider/Source. What types are supported, is documented in the individual Provider/Source. Returning `None` is always accepted, this simply skips this mapping.

!!! notice
    These variables are available in addition to the common variables/functions defined in [**Expressions**](../expressions/index.md)

### Context Variables

- `user`: The current user, this might be `None` if there is no contextual user. ([ref](../expressions/reference/user-object.md))
- `request`: The current request, this might be `None` if there is no contextual request. ([ref](https://docs.djangoproject.com/en/3.0/ref/request-response/#httprequest-objects))
- Arbitrary other arguments given by the provider, this is documented on the Provider/Source.
