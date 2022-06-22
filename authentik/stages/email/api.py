"""EmailStage API Views"""
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import TypeCreateSerializer
from authentik.flows.api.stages import StageSerializer
from authentik.stages.email.models import EmailStage, get_template_choices


class EmailStageSerializer(StageSerializer):
    """EmailStage Serializer"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["template"].choices = get_template_choices()

    def validate_template(self, value: str) -> str:
        """Check validity of template"""
        choices = get_template_choices()
        for path, _ in choices:
            if path == value:
                return value
        raise ValidationError(f"Invalid template '{value}' specified.")

    class Meta:

        model = EmailStage
        fields = StageSerializer.Meta.fields + [
            "use_global_settings",
            "host",
            "port",
            "username",
            "password",
            "use_tls",
            "use_ssl",
            "timeout",
            "from_address",
            "token_expiry",
            "subject",
            "template",
            "activate_user_on_success",
        ]
        extra_kwargs = {"password": {"write_only": True}}


class EmailStageViewSet(UsedByMixin, ModelViewSet):
    """EmailStage Viewset"""

    queryset = EmailStage.objects.all()
    serializer_class = EmailStageSerializer
    filterset_fields = [
        "name",
        "use_global_settings",
        "host",
        "port",
        "username",
        "use_tls",
        "use_ssl",
        "timeout",
        "from_address",
        "token_expiry",
        "subject",
        "template",
        "activate_user_on_success",
    ]
    search_fields = ["name"]
    ordering = ["name"]

    @extend_schema(responses={200: TypeCreateSerializer(many=True)})
    @action(detail=False, pagination_class=None, filter_backends=[])
    def templates(self, request: Request) -> Response:
        """Get all available templates, including custom templates"""
        choices = []
        for value, label in get_template_choices():
            choices.append(
                {
                    "name": value,
                    "description": label,
                    "component": "",
                    "model_name": "",
                }
            )
        return Response(TypeCreateSerializer(choices, many=True).data)
