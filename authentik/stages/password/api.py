"""PasswordStage API Views"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.flows.api.stages import StageSerializer
from authentik.stages.password.models import PasswordDevice, PasswordStage


class PasswordDeviceSerializer(ModelSerializer):
    """Safe metadata for a user's password device."""

    class Meta:
        model = PasswordDevice
        fields = [
            "pk",
            "name",
            "stage",
            "confirmed",
            "created",
            "last_updated",
            "last_used",
            "password_change_date",
        ]
        read_only_fields = fields


class PasswordStageSerializer(StageSerializer):
    """PasswordStage Serializer"""

    class Meta:
        model = PasswordStage
        fields = StageSerializer.Meta.fields + [
            "backends",
            "configure_flow",
            "failed_attempts_before_cancel",
            "allow_show_password",
        ]


class PasswordStageViewSet(UsedByMixin, ModelViewSet):
    """PasswordStage Viewset"""

    queryset = PasswordStage.objects.all()
    serializer_class = PasswordStageSerializer
    filterset_fields = [
        "name",
        "configure_flow",
        "failed_attempts_before_cancel",
        "allow_show_password",
    ]
    search_fields = ["name"]
    ordering = ["name"]
