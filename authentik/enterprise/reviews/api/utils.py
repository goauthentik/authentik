from django.contrib.contenttypes.models import ContentType
from rest_framework.serializers import ChoiceField, Serializer, UUIDField


def parse_content_type(value: str) -> dict:
    app_label, model = value.split(".")
    return {"app_label": app_label, "model": model}


def model_choices() -> list[tuple[str, str]]:
    return [
        ("authentik_core.application", "Application"),
        ("authentik_core.group", "Group"),
        ("authentik_rbac.role", "Role"),
    ]


class ContentTypeField(ChoiceField):
    def __init__(self, **kwargs):
        super().__init__(choices=model_choices(), **kwargs)

    def to_representation(self, content_type: ContentType) -> str:
        return f"{content_type.app_label}.{content_type.model}"

    def to_internal_value(self, data: str) -> ContentType:
        return ContentType.objects.get(**parse_content_type(data))


class GenericForeignKeySerializer(Serializer):
    content_type = ContentTypeField()
    object_id = UUIDField()
