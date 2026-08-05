"""PasswordStage API Views"""

from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.enterprise.license import LicenseKey
from authentik.flows.api.stages import StageSerializer
from authentik.stages.password.models import PasswordStage


class PasswordStageSerializer(StageSerializer):
    """PasswordStage Serializer"""

    def validate_failed_attempts_before_lockout(self, limit: int) -> int:
        """Locking passwords is an enterprise feature"""
        if limit and not LicenseKey.cached_summary().status.is_valid:
            raise ValidationError(_("Enterprise is required to lock passwords."))
        return limit

    class Meta:
        model = PasswordStage
        fields = StageSerializer.Meta.fields + [
            "backends",
            "configure_flow",
            "failed_attempts_before_cancel",
            "failed_attempts_before_lockout",
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
