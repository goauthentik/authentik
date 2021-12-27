"""Create"""
from django.db.models.base import Model
from django.utils.translation import gettext_lazy as _

from authentik.blueprints.v2.operation import ModelOperation
from authentik.blueprints.v2.utils import template_dict


class CreateOperation(ModelOperation):
    """Create"""

    def apply(self) -> Model:
        create_dict = template_dict(self.resource._with, self.controller._template_context)
        create_dict["managed"] = self.controller.managed
        return self._model.objects.create(**create_dict)

    def __label__(self) -> str:
        return _(
            "Model creation operation: %(model_label)s"
            % {"model_label": self._model.Meta.verbose_name}
        )
