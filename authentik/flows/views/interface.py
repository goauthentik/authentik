"""Interface views"""

from typing import Any

from django.shortcuts import get_object_or_404
from ua_parser.user_agent_parser import Parse

from authentik.core.views.interface import InterfaceView
from authentik.flows.models import Flow


class FlowInterfaceView(InterfaceView):
    """Flow interface"""

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        kwargs["flow"] = get_object_or_404(Flow, slug=self.kwargs.get("flow_slug"))
        kwargs["inspector"] = "inspector" in self.request.GET
        return super().get_context_data(**kwargs)

    def compat_needs_sfe(self) -> bool:
        """Check if we need to use the simplified flow executor for compatibility"""
        ua = Parse(self.request.META.get("HTTP_USER_AGENT", ""))
        if ua["user_agent"]["family"] == "IE":
            return True
        if ua["user_agent"]["family"] == "Edge" and int(ua["user_agent"]["major"]) <= 18:  # noqa: PLR2004
            return True
        return False

    def get_template_names(self) -> list[str]:
        if self.compat_needs_sfe() or "sfe" in self.request.GET:
            return ["if/flow-sfe.html"]
        return ["if/flow.html"]
