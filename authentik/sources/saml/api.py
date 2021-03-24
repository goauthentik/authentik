"""SAMLSource API Views"""
from drf_yasg2.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.sources import SourceSerializer
from authentik.providers.saml.api import SAMLMetadataSerializer
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
            "signing_kp",
            "digest_algorithm",
            "signature_algorithm",
            "temporary_user_delete_after",
        ]


class SAMLSourceViewSet(ModelViewSet):
    """SAMLSource Viewset"""

    queryset = SAMLSource.objects.all()
    serializer_class = SAMLSourceSerializer
    lookup_field = "slug"

    @swagger_auto_schema(responses={200: SAMLMetadataSerializer(many=False)})
    @action(methods=["GET"], detail=True)
    # pylint: disable=unused-argument
    def metadata(self, request: Request, slug: str) -> Response:
        """Return metadata as XML string"""
        source = self.get_object()
        metadata = MetadataProcessor(source, request).build_entity_descriptor()
        return Response({"metadata": metadata})
