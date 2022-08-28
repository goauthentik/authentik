"""Apply Blueprint meta model"""
from rest_framework.exceptions import ValidationError
from rest_framework.fields import BooleanField, JSONField
from structlog.stdlib import get_logger

from authentik.blueprints.v1.meta.base import BaseMetaModel
from authentik.core.api.utils import PassiveSerializer, is_dict
from authentik.lib.models import SerializerModel

LOGGER = get_logger()


class ApplyBlueprintMetaSerializer(PassiveSerializer):
    """Serializer for meta apply blueprint model"""

    identifiers = JSONField(validators=[is_dict])
    required = BooleanField(default=True)

    def update(self, instance: "MetaApplyBlueprint", validated_data: dict) -> "MetaApplyBlueprint":
        from authentik.blueprints.models import BlueprintInstance
        from authentik.blueprints.v1.tasks import apply_blueprint

        identifiers = validated_data["identifiers"]
        required = validated_data["required"]
        instance = BlueprintInstance.objects.filter(**identifiers).first()
        if not instance:
            if required:
                raise ValidationError("Required blueprint does not exist")
            LOGGER.info("Blueprint does not exist, but not required")
            return MetaApplyBlueprint()
        LOGGER.debug("Applying blueprint from meta model", blueprint=instance)
        # pylint: disable=no-value-for-parameter
        apply_blueprint(str(instance.pk))
        return MetaApplyBlueprint()


class MetaApplyBlueprint(SerializerModel, BaseMetaModel):
    """Meta model to apply another blueprint"""

    @property
    def serializer(self) -> ApplyBlueprintMetaSerializer:
        return ApplyBlueprintMetaSerializer

    class Meta:

        abstract = True
