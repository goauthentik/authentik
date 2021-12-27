"""Update operation"""
from typing import TYPE_CHECKING

from deepmerge import always_merger
from django.db.models.base import Model
from django.db.models.query import QuerySet
from django.utils.translation import gettext_lazy as _

from authentik.blueprints.v2.operation import ModelOperation
from authentik.blueprints.v2.spec import BlueprintResource
from authentik.blueprints.v2.utils import template_dict

if TYPE_CHECKING:
    from authentik.blueprints.v2.deploy import BlueprintDeploymentController


class UpdateOperation(ModelOperation):
    """Update models"""

    found: QuerySet

    def __init__(
        self,
        controller: "BlueprintDeploymentController",
        model: type[Model],
        resource: BlueprintResource,
        found: QuerySet,
    ) -> None:
        super().__init__(controller, model, resource)
        self.found = found

    def apply(self) -> Model:
        update_dict = template_dict(self.resource._with, self.controller._template_context)
        if self.found.count() > 1:
            raise ValueError("Update operation only supports single objects")
        obj = self.found.first()
        for key, value in update_dict:
            current_value = getattr(obj, key, None)
            if isinstance(current_value, dict):
                final_attributes = {}
                always_merger.merge(final_attributes, current_value)
                always_merger.merge(final_attributes, value)
                setattr(obj, key, final_attributes)
            else:
                setattr(obj, key, final_attributes)
        setattr(obj, "managed", self.controller.managed)
        return obj

    def __label__(self) -> str:
        return _(
            "Model update operation: %(model_label)s"
            % {"model_label": self._model.Meta.verbose_name}
        )
