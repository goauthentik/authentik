"""passbook proxy views"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Model
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views import View
from guardian.shortcuts import get_objects_for_user
from structlog import get_logger
from yaml import safe_dump

from passbook import __version__
from passbook.core.models import User
from passbook.providers.proxy.models import ProxyProvider

ORIGINAL_URL = "HTTP_X_ORIGINAL_URL"
LOGGER = get_logger()


def get_object_for_user_or_404(user: User, perm: str, **filters) -> Model:
    """Wrapper that combines get_objects_for_user and get_object_or_404"""
    return get_object_or_404(get_objects_for_user(user, perm), **filters)


class DockerComposeView(LoginRequiredMixin, View):
    """Generate docker-compose yaml"""

    def get_compose(self, provider: ProxyProvider) -> str:
        """Generate docker-compose yaml, version 3.5"""
        issuer = provider.get_issuer(self.request)
        env = {
            "OAUTH2_PROXY_CLIENT_ID": provider.client_id,
            "OAUTH2_PROXY_CLIENT_SECRET": provider.client_secret,
            "OAUTH2_PROXY_REDIRECT_URL": f"{provider.external_host}/oauth2/callback",
            "OAUTH2_PROXY_OIDC_ISSUER_URL": issuer,
            "OAUTH2_PROXY_COOKIE_SECRET": provider.cookie_secret,
            "OAUTH2_PROXY_UPSTREAMS": provider.internal_host,
        }
        compose = {
            "version": "3.5",
            "services": {
                "passbook_gatekeeper": {
                    "image": f"beryju/passbook-proxy:{__version__}",
                    "ports": ["4180:4180", "4443:4443"],
                    "environment": env,
                }
            },
        }
        return safe_dump(compose, default_flow_style=False)

    def get(self, request: HttpRequest, provider_pk: int) -> HttpResponse:
        """Render docker-compose file"""
        provider: ProxyProvider = get_object_for_user_or_404(
            request.user, "passbook_providers_proxy.view_proxyprovider", pk=provider_pk,
        )
        response = HttpResponse()
        response.content_type = "application/x-yaml"
        response.content = self.get_compose(provider.pk)
        return response


class K8sManifestView(LoginRequiredMixin, View):
    """Generate K8s Deployment and SVC for proxy"""

    def get(self, request: HttpRequest, provider_pk: int) -> HttpResponse:
        """Render deployment template"""
        provider: ProxyProvider = get_object_for_user_or_404(
            request.user, "passbook_providers_proxy.view_proxyprovider", pk=provider_pk,
        )
        return render(
            request,
            "providers/proxy/k8s-manifest.yaml",
            {
                "provider": provider,
                "cookie_secret": provider.cookie_secret,
                "version": __version__,
                "issuer": provider.get_issuer(request),
            },
            content_type="text/yaml",
        )
