"""Property Mapping Evaluator"""

from types import CodeType
from typing import Any

from django.db.models import Model
from django.http import HttpRequest
from prometheus_client import Histogram

from authentik.common.expression.evaluator import BaseEvaluator
from authentik.common.utils.errors import exception_to_string
from authentik.core.expression.exceptions import SkipObjectException
from authentik.core.models import User
from authentik.events.models import Event, EventAction
from authentik.policies.types import PolicyRequest

PROPERTY_MAPPING_TIME = Histogram(
    "authentik_property_mapping_execution_time",
    "Evaluation time of property mappings",
    ["mapping_name"],
)


class PropertyMappingEvaluator(BaseEvaluator):
    """Custom Evaluator that adds some different context variables."""

    dry_run: bool
    model: Model
    _compiled: CodeType | None = None

    def __init__(
        self,
        model: Model,
        user: User | None = None,
        request: HttpRequest | None = None,
        dry_run: bool | None = False,
        **kwargs,
    ):
        self.model = model
        if hasattr(model, "name"):
            _filename = model.name
        else:
            _filename = str(model)
        super().__init__(filename=_filename)
        self.dry_run = dry_run
        self.set_context(user, request, **kwargs)

    def set_context(
        self,
        user: User | None = None,
        request: HttpRequest | None = None,
        **kwargs,
    ):
        req = PolicyRequest(user=User())
        req.obj = self.model
        if user:
            req.user = user
            self._context["user"] = user
        if request:
            req.http_request = request
            self._context["http_request"] = request
        req.context.update(**kwargs)
        self._context["request"] = req
        self._context.update(**kwargs)
        self._globals["SkipObject"] = SkipObjectException

    def handle_error(self, exc: Exception, expression_source: str):
        """Exception Handler"""
        # For dry-run requests we don't save exceptions
        if self.dry_run:
            return
        error_string = exception_to_string(exc)
        event = Event.new(
            EventAction.PROPERTY_MAPPING_EXCEPTION,
            expression=expression_source,
            message=error_string,
        )
        if "request" in self._context:
            req: PolicyRequest = self._context["request"]
            if req.http_request:
                event.from_http(req.http_request, req.user)
                return
            elif req.user:
                event.set_user(req.user)
        event.save()

    def evaluate(self, *args, **kwargs) -> Any:
        with PROPERTY_MAPPING_TIME.labels(mapping_name=self._filename).time():
            return super().evaluate(*args, **kwargs)

    def compile(self, expression: str | None = None) -> Any:
        if not self._compiled:
            compiled = super().compile(expression or self.model.expression)
            self._compiled = compiled
        return self._compiled
