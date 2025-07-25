"""SAML Logout Stage API Views"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.flows.api.stages import StageSerializer
from authentik.stages.saml_logout.models import SAMLLogoutStage


class SAMLLogoutStageSerializer(StageSerializer):
    """SAMLLogoutStage Serializer"""

    class Meta:
        model = SAMLLogoutStage
        fields = StageSerializer.Meta.fields


class SAMLLogoutStageViewSet(UsedByMixin, ModelViewSet):
    """SAMLLogoutStage Viewset"""

    queryset = SAMLLogoutStage.objects.all()
    serializer_class = SAMLLogoutStageSerializer
    filterset_fields = ["name"]
    search_fields = ["name"]
    ordering = ["name"]
