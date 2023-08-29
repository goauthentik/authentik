"""Apply Blueprint meta model"""
from typing import TYPE_CHECKING

from rest_framework.exceptions import ValidationError
from rest_framework.fields import BooleanField, JSONField
from structlog.stdlib import get_logger

from authentik.blueprints.v1.meta.registry import BaseMetaModel, MetaResult, registry
from authentik.core.api.utils import PassiveSerializer, is_dict

if TYPE_CHECKING:
    from authentik.blueprints.models import BlueprintInstance

LOGGER = get_logger()


class ApplyBlueprintMetaSerializer(PassiveSerializer):
    """Serializer for meta apply blueprint model"""

    identifiers = JSONField(validators=[is_dict])
    required = BooleanField(default=True)

    # We cannot override `instance` as that will confuse rest_framework
    # and make it attempt to update the instance
    blueprint_instance: "BlueprintInstance"

    def validate(self, attrs):
        from authentik.blueprints.models import BlueprintInstance

        identifiers = attrs["identifiers"]
        required = attrs["required"]
        instance = BlueprintInstance.objects.filter(**identifiers).first()
        if not instance and required:
            raise ValidationError({"identifiers": "Required blueprint does not exist"})
        self.blueprint_instance = instance
        return super().validate(attrs)

    def create(self, validated_data: dict) -> MetaResult:
        from authentik.blueprints.v1.tasks import apply_blueprint

        if not self.blueprint_instance:
            LOGGER.info("Blueprint does not exist, but not required")
            return MetaResult()
        LOGGER.debug("Applying blueprint from meta model", blueprint=self.blueprint_instance)
        # pylint: disable=no-value-for-parameter
        apply_blueprint(str(self.blueprint_instance.pk))
        return MetaResult()


@registry.register("metaapplyblueprint")
class MetaApplyBlueprint(BaseMetaModel):
    """Meta model to apply another blueprint"""

    @staticmethod
    def serializer() -> ApplyBlueprintMetaSerializer:
        return ApplyBlueprintMetaSerializer

    class Meta:
        abstract = True
