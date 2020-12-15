"""Property Mapping Evaluator"""
from traceback import format_tb
from typing import Optional

from django.http import HttpRequest

from authentik.core.models import User
from authentik.events.models import Event, EventAction
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

    def handle_error(self, exc: Exception, expression_source: str):
        """Exception Handler"""
        error_string = "\n".join(format_tb(exc.__traceback__) + [str(exc)])
        event = Event.new(
            EventAction.PROPERTY_MAPPING_EXCEPTION,
            expression=expression_source,
            error=error_string,
            context=self._context,
        )
        if "request" in self._context:
            event.from_http(self._context["request"])
            return
        event.save()
