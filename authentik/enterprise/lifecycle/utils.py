from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from django.urls import reverse
from rest_framework.serializers import ChoiceField, Serializer, UUIDField, ModelSerializer

from authentik.core.models import Group, User, Application
from authentik.rbac.models import Role


def parse_content_type(value: str) -> dict:
    app_label, model = value.split(".")
    return {"app_label": app_label, "model": model}


def model_choices() -> list[tuple[str, str]]:
    return [
        ("authentik_core.application", "Application"),
        ("authentik_core.group", "Group"),
        ("authentik_rbac.role", "Role"),
    ]


def admin_link_for_model(model: Model) -> str:
    if isinstance(model, Application):
        return f"/core/applications/{model.slug}"
    elif isinstance(model, Group):
        return f"/identity/groups/{model.pk}"
    elif isinstance(model, Role):
        return f"/identity/roles/{model.pk}"
    else:
        raise TypeError("Unsupported model")


def link_for_model(model: Model) -> str:
    return f"{reverse("authentik_core:if-admin")}#{admin_link_for_model(model)}"


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


class ReviewerGroupSerializer(ModelSerializer):
    class Meta:
        model = Group
        fields = [
            "pk",
            "name",
        ]

class ReviewerUserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ["pk", "uuid", "username", "name"]
