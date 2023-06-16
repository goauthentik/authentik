"""SAMLSource API Views"""
from django.urls import reverse
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.sources import SourceSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.providers.saml.api.providers import SAMLMetadataSerializer
from authentik.sources.saml.models import SAMLSource
from authentik.sources.saml.processors.metadata import MetadataProcessor


class SAMLSourceSerializer(SourceSerializer):
    """SAMLSource Serializer"""

    class Meta:
        model = SAMLSource
        fields = SourceSerializer.Meta.fields + [
            "pre_authentication_flow",
            "issuer",
            "sso_url",
            "slo_url",
            "allow_idp_initiated",
            "name_id_policy",
            "binding_type",
            "verification_kp",
            "signing_kp",
            "digest_algorithm",
            "signature_algorithm",
            "temporary_user_delete_after",
        ]


class SAMLSourceViewSet(UsedByMixin, ModelViewSet):
    """SAMLSource Viewset"""

    queryset = SAMLSource.objects.all()
    serializer_class = SAMLSourceSerializer
    lookup_field = "slug"
    filterset_fields = [
        "name",
        "slug",
        "enabled",
        "authentication_flow",
        "enrollment_flow",
        "managed",
        "policy_engine_mode",
        "user_matching_mode",
        "pre_authentication_flow",
        "issuer",
        "sso_url",
        "slo_url",
        "allow_idp_initiated",
        "name_id_policy",
        "binding_type",
        "verification_kp",
        "signing_kp",
        "digest_algorithm",
        "signature_algorithm",
        "temporary_user_delete_after",
    ]
    search_fields = ["name", "slug"]
    ordering = ["name"]

    @extend_schema(responses={200: SAMLMetadataSerializer(many=False)})
    @action(methods=["GET"], detail=True)
    def metadata(self, request: Request, slug: str) -> Response:
        """Return metadata as XML string"""
        source = self.get_object()
        metadata = MetadataProcessor(source, request).build_entity_descriptor()
        return Response(
            {
                "metadata": metadata,
                "download_url": reverse(
                    "authentik_sources_saml:metadata",
                    kwargs={
                        "source_slug": source.slug,
                    },
                ),
            }
        )
