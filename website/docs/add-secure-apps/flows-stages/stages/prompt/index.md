---
title: Prompt stage
---

The Prompt stage prompts the user to enter information. The submitted values are then stored in the flow context.

## Overview

Use this stage to collect user input, such as profile attributes, passwords, invitation tokens, file uploads, or approval choices.

Submitted values are written to `prompt_data` in the flow context and can be consumed by later stages or policies.

## Configuration options

### Stage options

- **Fields**: the ordered set of prompt definitions included in the stage.
- **Validation policies**: optional policies evaluated after submission to validate the entered data.

### Prompt field types

Each prompt field can use one of these types:

| Type                  | Description                                                          |
| --------------------- | -------------------------------------------------------------------- |
| Text                  | Arbitrary text input.                                                |
| Text (read-only)      | Text displayed but not editable.                                     |
| Text area             | Multiline text input.                                                |
| Text area (read-only) | Multiline text displayed but not editable.                           |
| Username              | Text input with username uniqueness checks.                          |
| Email                 | Text input validated as an email address.                            |
| Password              | Masked input. Multiple password fields in the same stage must match. |
| Number                | Numeric input.                                                       |
| Checkbox              | Boolean checkbox input.                                              |
| Radio Button Group    | Single-choice selection rendered as radio buttons.                   |
| Dropdown              | Single-choice selection rendered as a dropdown.                      |
| Date                  | Date picker.                                                         |
| Date-time             | Date and time picker.                                                |
| File                  | File upload stored in flow context as a data URI.                    |
| Separator             | Static separator element.                                            |
| Hidden                | Hidden value inserted into the form submission.                      |
| Static                | Static value displayed as-is.                                        |
| authentik: Locale     | Locale selector populated from authentik-supported locales.          |

### Prompt field attributes

Each prompt field definition includes these core attributes:

- **field_key**: key used to store the field value in `prompt_data`.
- **label**: label shown to the user.
- **required**: whether the field must be provided.
- **placeholder**: placeholder text, or for choice fields, the available choices.
- **initial value**: pre-filled value, or for choice fields, the default selected choice.
- **order**: numeric ordering among the prompt fields.
- **Interpret placeholder as expression**: evaluate the placeholder dynamically.
- **Interpret initial value as expression**: evaluate the initial value dynamically.

For **Radio Button Group** and **Dropdown**, the placeholder defines the valid choices. It can be a plain string, a list of values, or a list of objects with `label` and `value`.

Some field types also have special behavior:

- **Username** checks for uniqueness.
- **Password** fields within the same stage must all match.
- **Hidden** and **Static** use their configured values without user editing.
- **Radio Button Group** and **Dropdown** only allow values from the defined choice set.

## Flow integration

Use this stage anywhere a flow needs user-provided input.

Common follow-up stages include:

- [User Write](../user_write/index.md) to persist collected values
- [Email](../email/index.md) or [Invitation](../invitation/index.md) to act on collected data
- policy checks that read from `request.context["prompt_data"]`

## Notes

### Accessing submitted data

Prompt values are stored in `prompt_data`:

```python
request.context.get("prompt_data", {}).get("<field_key>")
```

### Dynamic choices and defaults

For choice fields, placeholder and initial value can be generated dynamically with expressions. The prompt context is available during evaluation.

Choice fields also support context overrides:

- `<field_key>__choices` overrides the available choices
- `<field_key>` overrides the initial value

For `Radio Button Group` and `Dropdown`, choices can be plain values or objects like:

```python
return [
    "first option",
    42,
    {"label": "another option", "value": "some value"},
]
```

For fixed-choice fields, the default value must be one of the valid choices.

When prompt expressions are evaluated, they run in the same general expression environment used by authentik mappings and policies and also have access to `prompt_context`.

### Validation

Additional validation can be done with validation policies bound directly to the Prompt stage. For example, to ensure two password fields match:

```python
if request.context["prompt_data"]["password"] == request.context["prompt_data"]["password_repeat"]:
    return True

ak_message("Passwords don't match.")
return False
```
