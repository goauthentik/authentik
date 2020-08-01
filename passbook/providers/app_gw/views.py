"""passbook app_gw views"""
import string
from random import SystemRandom
from urllib.parse import urlparse

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Model
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views import View
from guardian.shortcuts import get_objects_for_user
from oidc_provider.lib.utils.common import get_issuer, get_site_url
from structlog import get_logger
from yaml import safe_dump

from passbook import __version__
from passbook.core.models import User
from passbook.providers.app_gw.models import ApplicationGatewayProvider

ORIGINAL_URL = "HTTP_X_ORIGINAL_URL"
LOGGER = get_logger()


def get_object_for_user_or_404(user: User, perm: str, **filters) -> Model:
    """Wrapper that combines get_objects_for_user and get_object_or_404"""
    return get_object_or_404(get_objects_for_user(user, perm), **filters)


def get_cookie_secret():
    """Generate random 32-character string for cookie-secret"""
    return "".join(
        SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(32)
    )


class DockerComposeView(LoginRequiredMixin, View):
    """Generate docker-compose yaml"""

    def get_compose(self, provider: ApplicationGatewayProvider) -> str:
        """Generate docker-compose yaml, version 3.5"""
        site_url = get_site_url(request=self.request)
        issuer = get_issuer(site_url=site_url, request=self.request)
        env = {
            "OAUTH2_PROXY_CLIENT_ID": provider.client.client_id,
            "OAUTH2_PROXY_CLIENT_SECRET": provider.client.client_secret,
            "OAUTH2_PROXY_REDIRECT_URL": f"{provider.external_host}/oauth2/callback",
            "OAUTH2_PROXY_OIDC_ISSUER_URL": issuer,
            "OAUTH2_PROXY_COOKIE_SECRET": get_cookie_secret(),
            "OAUTH2_PROXY_UPSTREAMS": provider.internal_host,
        }
        if urlparse(provider.external_host).scheme != "https":
            env["OAUTH2_PROXY_COOKIE_SECURE"] = "false"
        compose = {
            "version": "3.5",
            "services": {
                "passbook_gatekeeper": {
                    "image": f"beryju/passbook-gatekeeper:{__version__}",
                    "ports": ["4180:4180"],
                    "environment": env,
                }
            },
        }
        return safe_dump(compose, default_flow_style=False)

    def get(self, request: HttpRequest, provider_pk: int) -> HttpResponse:
        """Render docker-compose file"""
        provider: ApplicationGatewayProvider = get_object_for_user_or_404(
            request.user,
            "passbook_providers_app_gw.view_applicationgatewayprovider",
            pk=provider_pk,
        )
        response = HttpResponse()
        response.content_type = "application/x-yaml"
        response.content = self.get_compose(provider.pk)
        return response


class K8sManifestView(LoginRequiredMixin, View):
    """Generate K8s Deployment and SVC for gatekeeper"""

    def get(self, request: HttpRequest, provider_pk: int) -> HttpResponse:
        """Render deployment template"""
        provider: ApplicationGatewayProvider = get_object_for_user_or_404(
            request.user,
            "passbook_providers_app_gw.view_applicationgatewayprovider",
            pk=provider_pk,
        )
        site_url = get_site_url(request=self.request)
        issuer = get_issuer(site_url=site_url, request=self.request)
        return render(
            request,
            "app_gw/k8s-manifest.yaml",
            {
                "provider": provider,
                "cookie_secret": get_cookie_secret(),
                "version": __version__,
                "issuer": issuer,
            },
            content_type="text/yaml",
        )
