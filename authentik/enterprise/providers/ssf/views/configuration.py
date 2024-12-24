from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework.permissions import AllowAny

from authentik.core.models import Application
from authentik.enterprise.providers.ssf.models import DeliveryMethods, SSFProvider
from authentik.enterprise.providers.ssf.views.base import SSFView


class ConfigurationView(SSFView):
    permission_classes = [AllowAny]

    def get_authenticators(self):
        return []

    def get(
        self, request: HttpRequest, application_slug: str, provider: int, *args, **kwargs
    ) -> HttpResponse:
        application = get_object_or_404(Application, slug=application_slug)
        provider = get_object_or_404(SSFProvider, pk=provider)
        data = {
            "spec_version": "1_0-ID2",
            "issuer": self.request.build_absolute_uri(
                reverse(
                    "authentik_providers_ssf:configuration",
                    kwargs={
                        "application_slug": application.slug,
                        "provider": provider.pk,
                    },
                )
            ),
            "jwks_uri": self.request.build_absolute_uri(
                reverse(
                    "authentik_providers_ssf:jwks",
                    kwargs={
                        "provider": provider.pk,
                    },
                )
            ),
            "configuration_endpoint": self.request.build_absolute_uri(
                reverse(
                    "authentik_providers_ssf:stream",
                    kwargs={
                        "application_slug": application.slug,
                        "provider": provider.pk,
                    },
                )
            ),
            "delivery_methods_supported": [
                DeliveryMethods.RISC_PUSH,
            ],
            "authorization_schemes": [{"spec_urn": "urn:ietf:rfc:6749"}],
        }
        return JsonResponse(data)
