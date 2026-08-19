"""Interface views"""

from typing import Any

from django.shortcuts import get_object_or_404
from ua_parser.user_agent_parser import Parse

from authentik.core.views.interface import InterfaceView
from authentik.flows.models import Flow

# Oldest WebKit that can parse the default flow executor bundle. Earlier versions
# fail to parse it and render an empty page, so they are sent to the simplified
# flow executor instead.
MIN_WEBKIT_VERSION = (16, 4)


def version_below(version: dict[str, Any], minimum: tuple[int, int]) -> bool:
    """Check whether a parsed major/minor version is below minimum.

    Returns False when the version is missing or not numeric, so an unrecognised
    user agent keeps the default flow executor.
    """
    try:
        major = int(version["major"])
        minor = int(version["minor"] or 0)
    except (KeyError, TypeError, ValueError):
        return False
    return (major, minor) < minimum


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
        # Every browser on iOS renders through the system WebKit, so the iOS version
        # decides whether the bundle can be parsed regardless of which browser the
        # user opened.
        if ua["os"]["family"] == "iOS" and version_below(ua["os"], MIN_WEBKIT_VERSION):
            return True
        # iPadOS in desktop mode reports itself as Safari on macOS, which the check
        # above does not cover.
        if ua["user_agent"]["family"] in ("Safari", "Mobile Safari") and version_below(
            ua["user_agent"], MIN_WEBKIT_VERSION
        ):
            return True
        return False

    def get_template_names(self) -> list[str]:
        if self.compat_needs_sfe() or "sfe" in self.request.GET:
            return ["if/flow-sfe.html"]
        return ["if/flow.html"]
