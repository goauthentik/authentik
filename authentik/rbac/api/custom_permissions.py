from re import compile as re_compile

from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, SerializerMethodField
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.utils import ModelSerializer
from authentik.rbac.models import CUSTOM_PERMISSION_PREFIX, CustomPermission

CODENAME = re_compile(rf"{CUSTOM_PERMISSION_PREFIX}[a-z0-9_]+")


class ModelLabelField(CharField):
    """The content type of an authentik model, as app_label.model_name"""

    def to_representation(self, content_type: ContentType) -> str:
        return f"{content_type.app_label}.{content_type.model}"

    def to_internal_value(self, data) -> ContentType:
        app_label, dot, model = super().to_internal_value(data).partition(".")
        content_type = ContentType.objects.filter(app_label=app_label, model=model).first()
        if not dot or content_type is None or not app_label.startswith("authentik"):
            raise ValidationError(_("Unknown model."))
        return content_type


class CustomPermissionSerializer(ModelSerializer):
    model = ModelLabelField(source="content_type")
    permission = SerializerMethodField()

    def get_permission(self, instance: CustomPermission) -> str:
        return f"{instance.content_type.app_label}.{instance.codename}"

    def validate_codename(self, codename: str) -> str:
        if self.instance and codename != self.instance.codename:
            raise ValidationError(_("This cannot change."))
        if not CODENAME.fullmatch(codename):
            raise ValidationError(
                _("Start with custom_, followed by lowercase letters, digits, and underscores.")
            )
        return codename

    def validate_model(self, content_type: ContentType) -> ContentType:
        if self.instance and content_type != self.instance.content_type:
            raise ValidationError(_("This cannot change."))
        return content_type

    class Meta:
        model = CustomPermission
        fields = ["pk", "codename", "name", "model", "permission"]


class CustomPermissionViewSet(ModelViewSet):
    """Custom permissions"""

    queryset = CustomPermission.objects.select_related("content_type")
    serializer_class = CustomPermissionSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["codename"]
    search_fields = ["codename", "name"]
    ordering = ["codename"]
