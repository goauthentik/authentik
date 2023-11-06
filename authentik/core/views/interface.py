"""Interface views"""
from json import dumps
from typing import Any

from django.shortcuts import get_object_or_404
from django.views.generic.base import TemplateView
from rest_framework.request import Request

from authentik import get_build_hash
from authentik.admin.tasks import LOCAL_VERSION
from authentik.api.v3.config import ConfigView
from authentik.brands.api import CurrentBrandSerializer
from authentik.flows.models import Flow


class InterfaceView(TemplateView):
    """Base interface view"""

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        kwargs["config_json"] = dumps(ConfigView(request=Request(self.request)).get_config().data)
        kwargs["brand_json"] = dumps(CurrentBrandSerializer(self.request.brand).data)
        kwargs["version_family"] = f"{LOCAL_VERSION.major}.{LOCAL_VERSION.minor}"
        kwargs["version_subdomain"] = f"version-{LOCAL_VERSION.major}-{LOCAL_VERSION.minor}"
        kwargs["build"] = get_build_hash()
        return super().get_context_data(**kwargs)


class FlowInterfaceView(InterfaceView):
    """Flow interface"""

    template_name = "if/flow.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        kwargs["flow"] = get_object_or_404(Flow, slug=self.kwargs.get("flow_slug"))
        kwargs["inspector"] = "inspector" in self.request.GET
        return super().get_context_data(**kwargs)
