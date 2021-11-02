---
title: Prompt stage
---

This stage is used to show the user arbitrary prompts.

## Prompt

The prompt can be any of the following types:

| Type     | Description                                                       |
| -------- | ----------------------------------------------------------------- |
| text     | Arbitrary text. No client-side validation is done.                |
| email    | Email input. Requires a valid email address.                       |
| password | Password input.                                                   |
| number   | Number input. Any number is allowed.                              |
| checkbox | Simple checkbox.                                                  |
| hidden   | Hidden input field. Allows for the pre-setting of default values. |

A prompt has the following attributes:

### `field_key`

The HTML name used for the prompt. This key is also used to later retrieve the data in expression policies:

```python
request.context.get('prompt_data').get('<field_key>')
```

### `label`

The label used to describe the field. Depending on the selected template, this may not be shown.

### `required`

A flag which decides whether or not this field is required.

### `placeholder`

A field placeholder, shown within the input field. This field is also used by the `hidden` type as the actual value.

### `order`

The numerical index of the prompt. This applies to all stages which this prompt is a part of.

# Validation

Further validation of prompts can be done using policies.

To validate that two password fields are identical, create the following expression policy:

```python
if request.context.get('prompt_data').get('password') == request.context.get('prompt_data').get('password_repeat'):
    return True

ak_message("Passwords don't match.")
return False
```

This policy expects you to have two password fields with `field_key` set to `password` and `password_repeat`.

Afterwards, bind this policy to the prompt stage you want to validate.
