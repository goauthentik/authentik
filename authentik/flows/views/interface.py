"""Interface views"""

from typing import Any

from django.shortcuts import get_object_or_404
from ua_parser.user_agent_parser import Parse

from authentik.core.views.interface import InterfaceView
from authentik.flows.models import Flow, FlowDesignation
from authentik.flows.views.executor import SESSION_KEY_AUTH_STARTED


class FlowInterfaceView(InterfaceView):
    """Flow interface"""

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        flow = get_object_or_404(Flow, slug=self.kwargs.get("flow_slug"))
        kwargs["flow"] = flow
        if (
            not self.request.user.is_authenticated
            and flow.designation == FlowDesignation.AUTHENTICATION
        ):
            self.request.session[SESSION_KEY_AUTH_STARTED] = True
            self.request.session.save()
        kwargs["inspector"] = "inspector" in self.request.GET
        return super().get_context_data(**kwargs)

    def compat_needs_sfe(self) -> bool:
        """Check if we need to use the simplified flow executor for compatibility"""
        ua = Parse(self.request.META.get("HTTP_USER_AGENT", ""))
        if ua["user_agent"]["family"] == "IE":
            return True
        # Only use SFE for Edge 18 and older, after Edge 18 MS switched to chromium which supports
        # the default flow executor
        if (
            ua["user_agent"]["family"] == "Edge"
            and int(ua["user_agent"]["major"]) <= 18  # noqa: PLR2004
        ):  # noqa: PLR2004
            return True
        # https://github.com/AzureAD/microsoft-authentication-library-for-objc
        # Used by Microsoft Teams/Office on macOS, and also uses a very outdated browser engine
        if "PKeyAuth" in ua["string"]:
            return True
        return False

    def get_template_names(self) -> list[str]:
        if self.compat_needs_sfe() or "sfe" in self.request.GET:
            return ["if/flow-sfe.html"]
        return ["if/flow.html"]
