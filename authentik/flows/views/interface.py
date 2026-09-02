"""Interface views"""

from typing import Any

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from ua_parser.user_agent_parser import Parse

from authentik.core.views.interface import InterfaceView
from authentik.flows.models import Flow
from authentik.lib.http_cache import patch_anonymous_shared_cache

_STABLE_MEDIA_PREFIXES = ("/static/", "http://", "https://")


class FlowInterfaceView(InterfaceView):
    """Flow interface"""

    flow: Flow

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        self.flow = get_object_or_404(Flow, slug=self.kwargs.get("flow_slug"))
        kwargs["flow"] = self.flow
        kwargs["flow_background_url"] = self.flow.background_url(self.request)
        kwargs["inspector"] = "inspector" in self.request.GET
        if self._can_edge_cache(self.request):
            # Reusing server-generated trace metadata would combine unrelated clients'
            # browser spans into the trace which originally populated the cache.
            kwargs["html_meta"] = {}
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

    @staticmethod
    def _stable_media(value: object) -> bool:
        return not value or str(value).startswith(_STABLE_MEDIA_PREFIXES)

    def _can_edge_cache(self, request: HttpRequest) -> bool:
        """Check whether all rendered request variants have safe shared-cache keys."""
        if request.method not in ("GET", "HEAD") or request.COOKIES:
            return False
        brand = request.brand
        media = (
            self.flow.background,
            brand.branding_logo,
            brand.branding_favicon,
            brand.branding_default_flow_background,
        )
        return (
            "inspector" not in request.GET
            and "sfe" not in request.GET
            and not self.compat_needs_sfe()
            and all(self._stable_media(value) for value in media)
        )

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        response = super().dispatch(request, *args, **kwargs)
        if self._can_edge_cache(request):
            patch_anonymous_shared_cache(response, "Accept-Language", "User-Agent")
        return response
