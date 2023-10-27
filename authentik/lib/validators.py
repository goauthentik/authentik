"""Serializer validators"""
from typing import Optional

from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import Serializer
from rest_framework.utils.representation import smart_repr


class RequiredTogetherValidator:
    """Serializer-level validator that ensures all fields in `fields` are only
    used together"""

    fields: list[str]
    requires_context = True
    message = _("The fields {field_names} must be used together.")

    def __init__(self, fields: list[str], message: Optional[str] = None) -> None:
        self.fields = fields
        self.message = message or self.message

    def __call__(self, attrs: dict, serializer: Serializer):
        """Check that if any of the fields in `self.fields` are set, all of them must be set"""
        if any(field in attrs for field in self.fields) and not all(
            field in attrs for field in self.fields
        ):
            field_names = ", ".join(self.fields)
            message = self.message.format(field_names=field_names)
            raise ValidationError(message, code="required")

    def __repr__(self):
        return "<%s(fields=%s)>" % (self.__class__.__name__, smart_repr(self.fields))
