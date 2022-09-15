"""Property Mapping Evaluator"""
from traceback import format_tb
from typing import Optional

from django.db.models import Model
from django.http import HttpRequest
from guardian.utils import get_anonymous_user

from authentik.core.models import User
from authentik.events.models import Event, EventAction
from authentik.lib.expression.evaluator import BaseEvaluator
from authentik.policies.types import PolicyRequest


class PropertyMappingEvaluator(BaseEvaluator):
    """Custom Evaluator that adds some different context variables."""

    def __init__(
        self,
        model: Model,
        user: Optional[User] = None,
        request: Optional[HttpRequest] = None,
        **kwargs,
    ):
        if hasattr(model, "name"):
            _filename = model.name
        else:
            _filename = str(model)
        super().__init__(filename=_filename)
        req = PolicyRequest(user=get_anonymous_user())
        req.obj = model
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
