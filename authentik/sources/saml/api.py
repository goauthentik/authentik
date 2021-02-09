"""SAMLSource API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.sources import SourceSerializer
from authentik.sources.saml.models import SAMLSource


class SAMLSourceSerializer(SourceSerializer):
    """SAMLSource Serializer"""

    class Meta:

        model = SAMLSource
        fields = SourceSerializer.Meta.fields + [
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
