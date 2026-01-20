"""WSFederationProvider API Views"""

from django.http import HttpRequest
from django.urls import reverse
from rest_framework.fields import SerializerMethodField, URLField

from authentik.core.api.providers import ProviderSerializer
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.providers.ws_federation.models import WSFederationProvider
from authentik.enterprise.providers.ws_federation.processors.metadata import MetadataProcessor
from authentik.providers.saml.api.providers import SAMLProviderSerializer, SAMLProviderViewSet


class WSFederationProviderSerializer(EnterpriseRequiredMixin, SAMLProviderSerializer):
    """WSFederationProvider Serializer"""

    reply_url = URLField(source="acs_url")
    url_wsfed = SerializerMethodField()

    def get_url_wsfed(self, instance: WSFederationProvider) -> str:
        """Get WS-Fed url"""
        if "request" not in self._context:
            return ""
        request: HttpRequest = self._context["request"]._request
        return request.build_absolute_uri(reverse("authentik_providers_ws_federation:wsfed"))

    class Meta(SAMLProviderSerializer.Meta):
        model = WSFederationProvider
        fields = ProviderSerializer.Meta.fields + [
            "reply_url",
            "assertion_valid_not_before",
            "assertion_valid_not_on_or_after",
            "session_valid_not_on_or_after",
            "property_mappings",
            "name_id_mapping",
            "authn_context_class_ref_mapping",
            "digest_algorithm",
            "signature_algorithm",
            "signing_kp",
            "encryption_kp",
            "sign_assertion",
            "sign_logout_request",
            "default_name_id_policy",
            "url_download_metadata",
            "url_wsfed",
        ]
        extra_kwargs = ProviderSerializer.Meta.extra_kwargs


class WSFederationProviderViewSet(SAMLProviderViewSet):
    """WSFederationProvider Viewset"""

    queryset = WSFederationProvider.objects.all()
    serializer_class = WSFederationProviderSerializer
    filterset_fields = "__all__"
    ordering = ["name"]
    search_fields = ["name"]

    metadata_generator_class = MetadataProcessor
