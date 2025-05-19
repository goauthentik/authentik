"""Mutual TLS Stage API Views"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.stages.mtls.models import MutualTLSStage
from authentik.flows.api.stages import StageSerializer


class MutualTLSStageSerializer(EnterpriseRequiredMixin, StageSerializer):
    """MutualTLSStage Serializer"""

    class Meta:
        model = MutualTLSStage
        fields = StageSerializer.Meta.fields + [
            "mode",
            "certificate_authorities",
            "cert_attribute",
            "user_attribute",
        ]


class MutualTLSStageViewSet(UsedByMixin, ModelViewSet):
    """MutualTLSStage Viewset"""

    queryset = MutualTLSStage.objects.all()
    serializer_class = MutualTLSStageSerializer
    filterset_fields = "__all__"
    ordering = ["name"]
    search_fields = ["name"]
