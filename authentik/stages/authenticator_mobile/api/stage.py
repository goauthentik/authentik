"""AuthenticatorMobileStage API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.flows.api.stages import StageSerializer
from authentik.stages.authenticator_mobile.models import AuthenticatorMobileStage


class AuthenticatorMobileStageSerializer(StageSerializer):
    """AuthenticatorMobileStage Serializer"""

    class Meta:
        model = AuthenticatorMobileStage
        fields = StageSerializer.Meta.fields + [
            "configure_flow",
            "friendly_name",
            "item_matching_mode",
            "cgw_endpoint",
        ]


class AuthenticatorMobileStageViewSet(UsedByMixin, ModelViewSet):
    """AuthenticatorMobileStage Viewset"""

    queryset = AuthenticatorMobileStage.objects.all()
    serializer_class = AuthenticatorMobileStageSerializer
    filterset_fields = [
        "name",
        "configure_flow",
    ]
    search_fields = ["name"]
    ordering = ["name"]
