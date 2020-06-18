# Prompt Stage

This stage is used to show the user arbitrary prompts.

## Prompt

The prompt can be any of the following types:

| Type     | Description                                                      |
|----------|------------------------------------------------------------------|
| text     | Arbitrary text. No client-side validation is done.               |
| email    | Email input. Requires a valid email adress.                      |
| password | Password input.                                                  |
| number   | Number input. Any number is allowed.                             |
| checkbox | Simple checkbox.                                                 |
| hidden   | Hidden input field. Allows for the pre-setting of default values.|

A prompt has the following attributes:

### `field_key`

The HTML name used for the prompt. This key is also used to later retrieve the data in expression policies:

```jinja2
{{ request.context.prompt_data.<field_key> }}
```

### `label`

The label used to describe the field. Depending on the selected template, this may not be shown.

### `required`

A flag which decides whether or not this field is required.

### `placeholder`

A field placeholder, shown within the input field. This field is also used by the `hidden` type as the actual value.

### `order`

The numerical index of the prompt. This applies to all stages which this prompt is a part of.
