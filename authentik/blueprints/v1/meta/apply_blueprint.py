"""Apply Blueprint meta model"""

from typing import TYPE_CHECKING

from rest_framework.exceptions import ValidationError
from rest_framework.fields import BooleanField
from structlog.stdlib import get_logger

from authentik.blueprints.v1.meta.registry import BaseMetaModel, MetaResult, registry
from authentik.core.api.utils import JSONDictField, PassiveSerializer

if TYPE_CHECKING:
    from authentik.blueprints.models import BlueprintInstance

LOGGER = get_logger()


class ApplyBlueprintMetaSerializer(PassiveSerializer):
    """Serializer for meta apply blueprint model"""

    identifiers = JSONDictField()
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
        from authentik.blueprints.v1.importer import Importer

        if not self.blueprint_instance:
            LOGGER.info("Blueprint does not exist, but not required")
            return MetaResult()
        LOGGER.debug("Applying blueprint from meta model", blueprint=self.blueprint_instance)

        # Apply blueprint directly using Importer to avoid task context requirements
        # and prevent deadlocks when called from within another blueprint task
        blueprint_content = self.blueprint_instance.retrieve()
        importer = Importer.from_string(blueprint_content, self.blueprint_instance.context)
        valid, logs = importer.validate()
        [log.log() for log in logs]
        if valid:
            importer.apply()
        return MetaResult()


@registry.register("metaapplyblueprint")
class MetaApplyBlueprint(BaseMetaModel):
    """Meta model to apply another blueprint"""

    @staticmethod
    def serializer() -> ApplyBlueprintMetaSerializer:
        return ApplyBlueprintMetaSerializer

    class Meta:
        abstract = True
