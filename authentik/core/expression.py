"""Property Mapping Evaluator"""
from typing import Optional

from django.http import HttpRequest

from authentik.core.models import User
from authentik.lib.expression.evaluator import BaseEvaluator


class PropertyMappingEvaluator(BaseEvaluator):
    """Custom Evalautor that adds some different context variables."""

    def set_context(
        self, user: Optional[User], request: Optional[HttpRequest], **kwargs
    ):
        """Update context with context from PropertyMapping's evaluate"""
        if user:
            self._context["user"] = user
        if request:
            self._context["request"] = request
        self._context.update(**kwargs)
