# Prompt Stage

This stage is used to show the user arbitrary prompts.

## Prompt

The prompt can be any of the following types:

|          |                                                                  |
|----------|------------------------------------------------------------------|
| text     | Arbitrary text, no client-side validation is done.               |
| email    | E-Mail input, requires a valid E-Mail adress                     |
| password | Password Input                                                   |
| number   | Number Input, any number is allowed                              |
| checkbox | Simple Checkbox                                                  |
| hidden   | Hidden Input field, allows for the pre-setting of default values |

A Prompt has the following attributes:

### `field_key`

HTML name used for the prompt. This key is also used to later retrieve the data in expression policies:

```python
request.context.get('prompt_data').get('<field_key>')
```

### `label`

Label used to describe the Field. This might not be shown depending on the template selected.

### `required`

Flag that decides whether or not this field is required.

### `placeholder`

Field placeholder, shown within the input field. This field is also used by the `hidden` type as the actual value.

### `order`

Numerical index of the prompt. This applies to all stages this prompt is a part of.
