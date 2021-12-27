"""Base operations"""
from typing import TYPE_CHECKING

from django.db.models import Model
from django.utils.translation import gettext_lazy as _

from authentik.blueprints.v2.spec import BlueprintResource

if TYPE_CHECKING:
    from authentik.blueprints.v2.deploy import BlueprintDeploymentController


class Operation:
    """Base operation"""

    controller: "BlueprintDeploymentController"
    resource: BlueprintResource

    def __init__(
        self, controller: "BlueprintDeploymentController", resource: BlueprintResource
    ) -> None:
        self.controller = controller
        self.resource = resource

    def apply(self):
        """Apply planned changes"""

    def __label__(self) -> str:
        return _("Empty Operation")


class ModelOperation(Operation):
    """Operation for django models"""

    _model: type[Model]

    def __init__(
        self,
        controller: "BlueprintDeploymentController",
        model: type[Model],
        resource: BlueprintResource,
    ) -> None:
        super().__init__(controller, resource)
        self._model = model
