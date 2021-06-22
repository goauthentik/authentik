"""Property Mapping Evaluator"""
from traceback import format_tb
from typing import Optional

from django.http import HttpRequest
from guardian.utils import get_anonymous_user

from authentik.core.models import PropertyMapping, User
from authentik.events.models import Event, EventAction
from authentik.lib.expression.evaluator import BaseEvaluator
from authentik.policies.types import PolicyRequest


class PropertyMappingEvaluator(BaseEvaluator):
    """Custom Evalautor that adds some different context variables."""

    def set_context(
        self,
        user: Optional[User],
        request: Optional[HttpRequest],
        mapping: PropertyMapping,
        **kwargs,
    ):
        """Update context with context from PropertyMapping's evaluate"""
        req = PolicyRequest(user=get_anonymous_user())
        req.obj = mapping
        if user:
            req.user = user
            self._context["user"] = user
        if request:
            req.http_request = request
        self._context["request"] = req
        self._context.update(**kwargs)

    def handle_error(self, exc: Exception, expression_source: str):
        """Exception Handler"""
        error_string = "\n".join(format_tb(exc.__traceback__) + [str(exc)])
        event = Event.new(
            EventAction.PROPERTY_MAPPING_EXCEPTION,
            expression=expression_source,
            message=error_string,
        )
        if "request" in self._context:
            req: PolicyRequest = self._context["request"]
            event.from_http(req.http_request, req.user)
            return
        event.save()
