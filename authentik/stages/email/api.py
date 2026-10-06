"""EmailStage API Views"""

from django.template import TemplateSyntaxError
from rest_framework.fields import CharField, ReadOnlyField
from rest_framework.serializers import ModelSerializer, ValidationError
from rest_framework.viewsets import ModelViewSet

from authentik.admin.files.validation import validate_upload_file_name
from authentik.core.api.used_by import UsedByMixin
from authentik.flows.api.stages import StageSerializer
from authentik.stages.email.loaders import email_engine
from authentik.stages.email.models import EmailStage, EmailTemplate


class EmailStageSerializer(StageSerializer):
    """EmailStage Serializer"""

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
            "recovery_max_attempts",
            "recovery_cache_timeout",
        ]
        extra_kwargs = {
            "password": {"write_only": True},
            "template": {"required": True, "allow_null": False},
        }


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


class EmailTemplateSerializer(ModelSerializer):
    """EmailTemplate Serializer"""

    path = CharField()
    display_name = ReadOnlyField()

    def validate(self, attrs: dict) -> dict:
        path = attrs.get("path", getattr(self.instance, "path", None))
        managed = attrs.get("managed", getattr(self.instance, "managed", None))
        conflicts = EmailTemplate.objects.filter(path=path, managed__isnull=managed is None)
        if self.instance:
            conflicts = conflicts.exclude(pk=self.instance.pk)
        if conflicts.exists():
            raise ValidationError({"path": "A template with this path already exists."})
        return super().validate(attrs)

    def validate_path(self, path: str) -> str:
        validate_upload_file_name(path, ValidationError=ValidationError)
        return path

    def validate_body(self, body: str) -> str:
        return self._validate_template(body)

    def validate_body_plaintext(self, body_plaintext: str) -> str:
        return self._validate_template(body_plaintext)

    def _validate_template(self, value: str) -> str:
        try:
            email_engine().from_string(value)
        except TemplateSyntaxError as exc:
            raise ValidationError(str(exc)) from exc
        return value

    class Meta:
        model = EmailTemplate
        fields = [
            "uuid",
            "path",
            "display_name",
            "description",
            "body",
            "body_plaintext",
            "managed",
        ]


class EmailTemplateViewSet(UsedByMixin, ModelViewSet):
    """EmailTemplate Viewset"""

    queryset = EmailTemplate.objects.all()
    serializer_class = EmailTemplateSerializer
    filterset_fields = ["path", "managed"]
    search_fields = ["path", "description"]
    ordering = ["path"]
