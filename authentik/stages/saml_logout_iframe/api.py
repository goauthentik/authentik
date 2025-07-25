"""SAML iframe logout stage API"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.flows.api.stages import StageSerializer
from authentik.stages.saml_logout_iframe.models import SAMLIframeLogoutStage


class SAMLIframeLogoutStageSerializer(StageSerializer):
    """SAMLIframeLogoutStage Serializer"""

    class Meta:
        model = SAMLIframeLogoutStage
        fields = StageSerializer.Meta.fields + ["iframe_timeout"]


class SAMLIframeLogoutStageViewSet(UsedByMixin, ModelViewSet):
    """SAMLIframeLogoutStage Viewset"""

    queryset = SAMLIframeLogoutStage.objects.all()
    serializer_class = SAMLIframeLogoutStageSerializer
    filterset_fields = "__all__"
    search_fields = ["name"]
    ordering = ["name"]
