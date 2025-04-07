"""API Utilities"""

from typing import Any

from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from drf_spectacular.extensions import OpenApiSerializerFieldExtension
from drf_spectacular.plumbing import build_basic_type
from drf_spectacular.types import OpenApiTypes
from guardian.shortcuts import assign_perm
from rest_framework.fields import (
    CharField,
    IntegerField,
    JSONField,
    SerializerMethodField,
)
from rest_framework.serializers import ModelSerializer as BaseModelSerializer
from rest_framework.serializers import (
    Serializer,
    ValidationError,
    model_meta,
    raise_errors_on_nested_writes,
)

from authentik.rbac.models import InitialPermissions, InitialPermissionsMode


def is_dict(value: Any):
    """Ensure a value is a dictionary, useful for JSONFields"""
    if isinstance(value, dict):
        return
    raise ValidationError("Value must be a dictionary, and not have any duplicate keys.")


class ModelSerializer(BaseModelSerializer):
    def create(self, validated_data):
        instance = super().create(validated_data)
        user = self.context["request"].user
        initial_permissions_list = InitialPermissions.objects.filter(
            role__group__in=user.groups.all()
        )

        # Performance here should not be an issue, but if needed, there are many optimization routes
        for initial_permissions in initial_permissions_list:
            for permission in initial_permissions.permissions.all():
                if permission.content_type != ContentType.objects.get_for_model(instance):
                    continue
                assign_to = (
                    user
                    if initial_permissions.mode == InitialPermissionsMode.USER
                    else initial_permissions.role.group
                )
                assign_perm(permission, assign_to, instance)

        return instance

    def update(self, instance: Model, validated_data):
        raise_errors_on_nested_writes("update", self, validated_data)
        info = model_meta.get_field_info(instance)

        # Simply set each attribute on the instance, and then save it.
        # Note that unlike `.create()` we don't need to treat many-to-many
        # relationships as being a special case. During updates we already
        # have an instance pk for the relationships to be associated with.
        m2m_fields = []
        for attr, value in validated_data.items():
            if attr in info.relations and info.relations[attr].to_many:
                m2m_fields.append((attr, value))
            else:
                setattr(instance, attr, value)

        instance.save()

        # Note that many-to-many fields are set after updating instance.
        # Setting m2m fields triggers signals which could potentially change
        # updated instance and we do not want it to collide with .update()
        for attr, value in m2m_fields:
            field = getattr(instance, attr)
            # We can't check for inheritance here as m2m managers are generated dynamically
            if field.__class__.__name__ == "RelatedManager":
                field.set(value, bulk=False)
            else:
                field.set(value)

        return instance


class JSONDictField(JSONField):
    """JSON Field which only allows dictionaries"""

    default_validators = [is_dict]


class JSONExtension(OpenApiSerializerFieldExtension):
    """Generate API Schema for JSON fields as"""

    target_class = "authentik.core.api.utils.JSONDictField"

    def map_serializer_field(self, auto_schema, direction):
        return build_basic_type(OpenApiTypes.OBJECT)


class PassiveSerializer(Serializer):
    """Base serializer class which doesn't implement create/update methods"""

    def create(self, validated_data: dict) -> Model:  # pragma: no cover
        return Model()

    def update(self, instance: Model, validated_data: dict) -> Model:  # pragma: no cover
        return Model()


class PropertyMappingPreviewSerializer(PassiveSerializer):
    """Preview how the current user is mapped via the property mappings selected in a provider"""

    preview = JSONDictField(read_only=True)


class MetaNameSerializer(PassiveSerializer):
    """Add verbose names to response"""

    verbose_name = SerializerMethodField()
    verbose_name_plural = SerializerMethodField()
    meta_model_name = SerializerMethodField()

    def get_verbose_name(self, obj: Model) -> str:
        """Return object's verbose_name"""
        return obj._meta.verbose_name

    def get_verbose_name_plural(self, obj: Model) -> str:
        """Return object's plural verbose_name"""
        return obj._meta.verbose_name_plural

    def get_meta_model_name(self, obj: Model) -> str:
        """Return internal model name"""
        return f"{obj._meta.app_label}.{obj._meta.model_name}"


class CacheSerializer(PassiveSerializer):
    """Generic cache stats for an object"""

    count = IntegerField(read_only=True)


class LinkSerializer(PassiveSerializer):
    """Returns a single link"""

    link = CharField()
