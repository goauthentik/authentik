"""Interface views"""

from typing import Any

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from ua_parser.user_agent_parser import Parse

from authentik.core.views.interface import InterfaceView
from authentik.flows.models import Flow
from authentik.lib.http_cache import anonymous_redirect_cache_control


class FlowInterfaceView(InterfaceView):
    """Flow interface"""

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        flow = get_object_or_404(Flow, slug=self.kwargs.get("flow_slug"))
        kwargs["flow"] = flow
        kwargs["flow_background_url"] = flow.background_url(self.request)
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

    def _can_edge_cache(self, request: HttpRequest) -> bool:
        """Whether the response is safe to mark as publicly cacheable.

        The body is deterministic per ``(host, flow_slug)`` only when:
        no session cookie, no SFE-selecting UA (IE, Edge<=18, PKeyAuth — we
        exclude them rather than ``Vary: User-Agent``), and no ``?sfe`` or
        ``?inspector`` query variants.
        """
        if settings.SESSION_COOKIE_NAME in request.COOKIES:
            return False
        if "inspector" in request.GET or "sfe" in request.GET:
            return False
        if self.compat_needs_sfe():
            return False
        return True

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        response = super().dispatch(request, *args, **kwargs)
        if self._can_edge_cache(request):
            response["Cache-Control"] = anonymous_redirect_cache_control()
        return response
