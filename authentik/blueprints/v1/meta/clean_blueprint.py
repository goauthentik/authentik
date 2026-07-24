"""Clean Blueprint meta model"""

from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField

from authentik.blueprints.v1.meta.registry import BaseMetaModel, MetaResult, registry
from authentik.core.api.utils import PassiveSerializer
from authentik.lib.models import SerializerModel


class CleanBlueprintMetaSerializer(PassiveSerializer):
    """Serializer for meta clean blueprint model"""

    model_name = CharField()

    model: type[SerializerModel]

    def validate(self, attrs):
        model_attr = attrs["model_name"]

        model_app_label, model_name = model_attr.split(".")
        try:
            mdl: type[SerializerModel] = registry.get_model(model_app_label, model_name)
        except LookupError as exc:
            raise ValidationError({"model_name": "Required model does not exist"}) from exc

        self.model = mdl

        return super().validate(attrs)

    def create(self, validated_data: dict) -> MetaResult:
        existing_objects = self.model.objects.all()

        existing_objects.delete()

        return MetaResult()


@registry.register("metacleanblueprint")
class MetaCleanBlueprint(BaseMetaModel):
    """Meta model to delete all instances of another model"""

    @staticmethod
    def serializer() -> CleanBlueprintMetaSerializer:
        return CleanBlueprintMetaSerializer

    class Meta:
        abstract = True
