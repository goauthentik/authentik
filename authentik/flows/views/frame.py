from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, cast

from django.http import HttpRequest, HttpResponse
from django.views import View
from django.views.decorators.clickjacking import xframe_options_sameorigin

from authentik.flows.models import Stage
from authentik.flows.planner import FlowPlan
from authentik.flows.views.executor import SESSION_KEY_PLAN


class FlowFrameView[T: Stage](View):
    """Base-class for views rendered in frames in flows"""

    stage: T

    def setup(self, request: HttpRequest, *args: Any, **kwargs: Any) -> None:
        super().setup(request, *args, **kwargs)
        with self.active_flow_plan() as plan:
            self.stage = cast(T, plan.bindings[0].stage)

    @xframe_options_sameorigin
    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        return super().dispatch(request, *args, **kwargs)

    @contextmanager
    def active_flow_plan(self) -> Generator[FlowPlan]:
        plan: FlowPlan = self.request.session[SESSION_KEY_PLAN]
        try:
            yield plan
        finally:
            self.request.session[SESSION_KEY_PLAN] = plan
