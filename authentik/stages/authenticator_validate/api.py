"""AuthenticatorValidateStage API Views"""
from rest_framework.serializers import ValidationError
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.flows.api.stages import StageSerializer
from authentik.flows.models import NotConfiguredAction
from authentik.stages.authenticator_validate.models import AuthenticatorValidateStage


class AuthenticatorValidateStageSerializer(StageSerializer):
    """AuthenticatorValidateStage Serializer"""

    def validate_configuration_stages(self, value):
        """Ensure that a configuration stage is set when not_configured_action is configure"""
        not_configured_action = self.initial_data.get("not_configured_action", [])
        if not_configured_action == NotConfiguredAction.CONFIGURE and len(value) < 1:
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
            "webauthn_user_verification",
        ]


class AuthenticatorValidateStageViewSet(UsedByMixin, ModelViewSet):
    """AuthenticatorValidateStage Viewset"""

    queryset = AuthenticatorValidateStage.objects.all()
    serializer_class = AuthenticatorValidateStageSerializer
    filterset_fields = ["name", "not_configured_action", "configuration_stages"]
    ordering = ["name"]
    search_fields = ["name"]
