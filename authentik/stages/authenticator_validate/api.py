"""AuthenticatorValidateStage API Views"""
from rest_framework.serializers import ValidationError
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.flows.api.stages import StageSerializer
from authentik.flows.models import NotConfiguredAction
from authentik.stages.authenticator_validate.models import AuthenticatorValidateStage


class AuthenticatorValidateStageSerializer(StageSerializer):
    """AuthenticatorValidateStage Serializer"""

    def validate_not_configured_action(self, value):
        """Ensure that a configuration stage is set when not_configured_action is configure"""
        configuration_stages = self.initial_data.get("configuration_stages")
        if value == NotConfiguredAction.CONFIGURE and configuration_stages is None:
            raise ValidationError(
                (
                    'When "Not configured action" is set to "Configure", '
                    "you must set a configuration stage."
                )
            )
        return value

    class Meta:

        model = AuthenticatorValidateStage
        fields = StageSerializer.Meta.fields + [
            "not_configured_action",
            "device_classes",
            "configuration_stages",
            "last_auth_threshold",
        ]


class AuthenticatorValidateStageViewSet(UsedByMixin, ModelViewSet):
    """AuthenticatorValidateStage Viewset"""

    queryset = AuthenticatorValidateStage.objects.all()
    serializer_class = AuthenticatorValidateStageSerializer
    filterset_fields = ["name", "not_configured_action", "configuration_stages"]
    ordering = ["name"]
    search_fields = ["name"]
