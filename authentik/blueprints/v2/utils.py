"""Utils"""
from typing import Any

from django.template import Template


# pylint: disable=redefined-builtin
def template_if_required(input: Any, **context) -> Any:
    """Render template if possible/required"""
    if isinstance(input, (int, float)):
        return input
    if "{{" in input:
        return Template(input).render(**context)
    return input


# pylint: disable=redefined-builtin
def template_dict(input: dict, context: dict) -> dict:
    """Run `template_if_required` over an entire dict"""
    new_dict = {}
    for key, value in input:
        if isinstance(value, dict):
            new_dict[key] = template_dict(input[key], context)
        elif isinstance(value, str):
            new_dict[key] = template_if_required(input[key], **context)
        else:
            new_dict[key] = value
    return new_dict
