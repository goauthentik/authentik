"""SAMLSource API Views"""
from authentik.core.api.utils import MetaNameSerializer
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.admin.forms.source import SOURCE_FORM_FIELDS
from authentik.sources.saml.models import SAMLSource


class SAMLSourceSerializer(ModelSerializer, MetaNameSerializer):
    """SAMLSource Serializer"""

    class Meta:

        model = SAMLSource
        fields = SOURCE_FORM_FIELDS + [
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
