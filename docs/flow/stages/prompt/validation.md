# Prompt Validation

Further validation of prompts can be done using policies.

To validate that two password fields are identical, create the following expression policy:

```jinja2
{% if request.context.prompt_data.password == request.context.prompt_data.password_repeat %}
True
{% else %}
{% do pb_message("Passwords don't match.") %}
False
{% endif %}
```
This policy expects you two have two password fields with `field_key` set to `password` and `password_repeat`.

Afterwards bind this policy to the prompt stage you want to validate.
