from typing import Any

from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, SerializerMethodField
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.utils import ModelSerializer
from authentik.core.models import AttributesMixin, ObjectAttribute
from authentik.lib.utils.dict import get_path_from_dict


class AttributesMixinSerializer(ModelSerializer):

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        model = self.Meta.model
        attrs = data.get("attributes", {})
        attributes = ObjectAttribute.objects.filter(
            object_type=ContentType.objects.get_for_model(model),
            enabled=True,
        )
        for attr in attributes:
            value = get_path_from_dict(attrs, attr.key)
            attr.run_validation(value)
        return data


class ContentTypeSerializer(ModelSerializer):
    app_label = CharField(read_only=True)
    model = CharField(read_only=True)
    verbose_name_plural = SerializerMethodField()
    fully_qualified_model = SerializerMethodField()

    def get_fully_qualified_model(self, ct: ContentType) -> str:
        return f"{ct.app_label}.{ct.model}"

    def get_verbose_name_plural(self, ct: ContentType) -> str:
        return ct.model_class()._meta.verbose_name_plural

    class Meta:
        model = ContentType
        fields = ("id", "app_label", "model", "verbose_name_plural", "fully_qualified_model")


class ObjectAttributeSerializer(ModelSerializer):

    object_type = CharField()
    object_type_obj = ContentTypeSerializer(read_only=True, source="object_type")

    def validate_object_type(self, fqm: str) -> ContentType:
        app_label, _, model = fqm.partition(".")
        ct = ContentType.objects.filter(app_label=app_label, model=model).first()
        if not ct or not issubclass(ct.model_class(), AttributesMixin):
            raise ValidationError("Invalid object type")
        return ct

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs.get("is_unique") and attrs.get("is_array"):
            raise ValidationError(_("Unique cannot be enabled for arrays."))
        return super().validate(attrs)

    class Meta:
        model = ObjectAttribute
        fields = [
            "pk",
            "object_type",
            "object_type_obj",
            "enabled",
            "created",
            "key",
            "label",
            "last_updated",
            "regex",
            "type",
            "group",
            "managed",
            "is_unique",
            "is_required",
            "is_array",
        ]
        extra_kwargs = {
            "last_updated": {"read_only": True},
            "created": {"read_only": True},
            "pk": {"read_only": True},
        }


class ObjectAttributeViewSet(ModelViewSet):
    serializer_class = ObjectAttributeSerializer
    queryset = ObjectAttribute.objects.all()
    filterset_fields = ["object_type__model", "object_type__app_label", "enabled"]
    search_fields = ["key", "label", "group", "object_type__model", "object_type__app_label"]
    ordering = ["key"]
