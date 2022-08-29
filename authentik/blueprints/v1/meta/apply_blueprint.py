"""Apply Blueprint meta model"""
from rest_framework.exceptions import ValidationError
from rest_framework.fields import BooleanField, JSONField
from structlog.stdlib import get_logger

from authentik.blueprints.v1.meta.registry import BaseMetaModel, MetaResult, registry
from authentik.core.api.utils import PassiveSerializer, is_dict

LOGGER = get_logger()


class ApplyBlueprintMetaSerializer(PassiveSerializer):
    """Serializer for meta apply blueprint model"""

    identifiers = JSONField(validators=[is_dict])
    required = BooleanField(default=True)

    def create(self, validated_data: dict) -> MetaResult:
        from authentik.blueprints.models import BlueprintInstance
        from authentik.blueprints.v1.tasks import apply_blueprint

        identifiers = validated_data["identifiers"]
        required = validated_data["required"]
        instance = BlueprintInstance.objects.filter(**identifiers).first()
        if not instance:
            if required:
                raise ValidationError("Required blueprint does not exist")
            LOGGER.info("Blueprint does not exist, but not required")
            return MetaResult()
        LOGGER.debug("Applying blueprint from meta model", blueprint=instance)
        # pylint: disable=no-value-for-parameter
        apply_blueprint(str(instance.pk))
        return MetaResult()


@registry.register("metaapplyblueprint")
class MetaApplyBlueprint(BaseMetaModel):
    """Meta model to apply another blueprint"""

    @staticmethod
    def serializer() -> ApplyBlueprintMetaSerializer:
        return ApplyBlueprintMetaSerializer

    class Meta:

        abstract = True
