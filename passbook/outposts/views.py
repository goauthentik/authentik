"""passbook outpost views"""
from typing import Any, Dict, List

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Model
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import TemplateView
from guardian.shortcuts import get_objects_for_user
from structlog import get_logger

from passbook.core.models import User
from passbook.outposts.controllers.docker import DockerController
from passbook.outposts.models import Outpost, OutpostType
from passbook.providers.proxy.controllers.kubernetes import ProxyKubernetesController

LOGGER = get_logger()


def get_object_for_user_or_404(user: User, perm: str, **filters) -> Model:
    """Wrapper that combines get_objects_for_user and get_object_or_404"""
    return get_object_or_404(get_objects_for_user(user, perm), **filters)


class DockerComposeView(LoginRequiredMixin, View):
    """Generate docker-compose yaml"""

    def get(self, request: HttpRequest, outpost_pk: str) -> HttpResponse:
        """Render docker-compose file"""
        outpost: Outpost = get_object_for_user_or_404(
            request.user,
            "passbook_outposts.view_outpost",
            pk=outpost_pk,
        )
        manifest = ""
        if outpost.type == OutpostType.PROXY:
            controller = DockerController(outpost)
            manifest = controller.get_static_deployment()

        return HttpResponse(manifest, content_type="text/vnd.yaml")


class KubernetesManifestView(LoginRequiredMixin, View):
    """Generate Kubernetes Deployment and SVC for proxy"""

    def get(self, request: HttpRequest, outpost_pk: str) -> HttpResponse:
        """Render deployment template"""
        outpost: Outpost = get_object_for_user_or_404(
            request.user,
            "passbook_outposts.view_outpost",
            pk=outpost_pk,
        )
        manifest = ""
        if outpost.type == OutpostType.PROXY:
            controller = ProxyKubernetesController(outpost)
            manifest = controller.get_static_deployment()

        return HttpResponse(manifest, content_type="text/vnd.yaml")


class SetupView(LoginRequiredMixin, TemplateView):
    """Setup view"""

    def get_template_names(self) -> List[str]:
        allowed = ["dc", "custom", "k8s_manual", "k8s_integration"]
        setup_type = self.request.GET.get("type", "dc")
        if setup_type not in allowed:
            setup_type = allowed[0]
        return [f"outposts/setup_{setup_type}.html"]

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        kwargs = super().get_context_data(**kwargs)
        outpost: Outpost = get_object_for_user_or_404(
            self.request.user,
            "passbook_outposts.view_outpost",
            pk=self.kwargs["outpost_pk"],
        )
        kwargs.update(
            {"host": self.request.build_absolute_uri("/"), "outpost": outpost}
        )
        return kwargs
