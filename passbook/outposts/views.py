"""passbook outpost views"""
from typing import Any, Dict, List
from uuid import UUID

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Model
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import TemplateView
from guardian.shortcuts import get_objects_for_user
from structlog import get_logger
from yaml import safe_dump

from passbook import __version__
from passbook.core.models import Token, User
from passbook.outposts.models import Outpost, OutpostType

LOGGER = get_logger()


def get_object_for_user_or_404(user: User, perm: str, **filters) -> Model:
    """Wrapper that combines get_objects_for_user and get_object_or_404"""
    return get_object_or_404(get_objects_for_user(user, perm), **filters)


class DockerComposeView(LoginRequiredMixin, View):
    """Generate docker-compose yaml"""

    token: Token

    def get_proxy_compose(self) -> str:
        """Generate docker-compose yaml for proxy, version 3.5"""
        compose = {
            "version": "3.5",
            "services": {
                "passbook_gatekeeper": {
                    "image": f"beryju/passbook-proxy:{__version__}",
                    "ports": ["4180:4180", "4443:4443"],
                    "environment": {
                        "PASSBOOK_HOST": self.request.build_absolute_uri("/"),
                        "PASSBOOK_TOKEN": self.token.pk.hex,
                    },
                }
            },
        }
        return safe_dump(compose, default_flow_style=False)

    def get(self, request: HttpRequest, outpost_pk: UUID) -> HttpResponse:
        """Render docker-compose file"""
        outpost: Outpost = get_object_for_user_or_404(
            request.user, "passbook_outposts.view_outpost", pk=outpost_pk,
        )
        # Ensure outpost has a token defined
        self.token = outpost.token

        response = HttpResponse()
        response.content_type = "application/x-yaml"
        if outpost.type == OutpostType.PROXY:
            response.content = self.get_proxy_compose()
        return response


class KubernetesManifestView(LoginRequiredMixin, View):
    """Generate Kubernetes Deployment and SVC for proxy"""

    token: Token

    def get(self, request: HttpRequest, outpost_pk: UUID) -> HttpResponse:
        """Render deployment template"""

        return render(
            request, "outposts/k8s-manifest.yaml", {}, content_type="text/yaml",
        )


class SetupView(LoginRequiredMixin, TemplateView):
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
        # Ensure outpost has a token defined
        token = outpost.token
        kwargs.update(
            {"host": self.request.build_absolute_uri("/"), "outpost": outpost,}
        )
        return kwargs
