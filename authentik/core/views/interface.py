"""Interface views"""
from typing import Any

from django.shortcuts import get_object_or_404
from django.views.generic.base import TemplateView

from authentik.flows.models import Flow


class FlowInterfaceView(TemplateView):
    """Flow interface"""

    template_name = "if/flow.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        kwargs["flow"] = get_object_or_404(Flow, slug=self.kwargs.get("flow_slug"))
        kwargs["inspector"] = "inspector" in self.request.GET
        return super().get_context_data(**kwargs)
