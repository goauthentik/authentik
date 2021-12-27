"""blueprint deployment controller"""
from typing import Optional

from django.apps import apps
from django.db.models import Model, Q
from structlog.stdlib import BoundLogger, get_logger

from authentik.blueprints.models import BlueprintInstance
from authentik.blueprints.v2.operation import Operation
from authentik.blueprints.v2.operation_create import CreateOperation
from authentik.blueprints.v2.operation_update import UpdateOperation
from authentik.blueprints.v2.spec import BlueprintFilter, BlueprintResource, BlueprintSpec
from authentik.blueprints.v2.utils import template_if_required


class BlueprintDeploymentController:
    """Apply and diff blueprints"""

    blueprint: BlueprintSpec
    instance: BlueprintInstance

    logger: BoundLogger

    _operations: list[Operation]
    _template_context: dict

    def __init__(self, instance: BlueprintInstance, blueprint: BlueprintSpec) -> None:
        self.blueprint = blueprint
        self.instance = instance
        self.logger = get_logger().bind(instance=self.instance)
        self._operations = []
        self._template_context = instance.context

    @property
    def managed(self) -> str:
        """Get managed flag for all objects to identify as belonging to us"""
        return f"goauthentik.io/blueprints/{self.instance.instance_uuid.hex}"

    def apply(self):
        """Apply all planned operations"""
        models = []
        # pylint: disable=invalid-name
        for op in self._operations:
            self.logger.debug("Running operation", op=op)
            apply_result = op.apply()
            if isinstance(apply_result, Model):
                models.append(apply_result)

    def compile(self):
        """Check and prepare all operations necessary"""
        for resource in self.blueprint.resources:
            # pylint: disable=invalid-name
            op = self._compile_single(resource)
            if op:
                self._operations.append(op)
        # TODO: Check for models with our managed attribute which aren't listed

    def _compile_single(self, resource: BlueprintResource) -> Optional[Operation]:
        # Ensure the model is loaded
        try:
            model: type[Model] = apps.get_model(*resource.model_name.split("."))
        except LookupError:
            return None
        compiled_filters = Q(
            managed=self.managed,
        )
        for _filter in resource.filters:
            compiled_filters &= self._compile_filter(resource, _filter)
        self.logger.debug("Searching for existing objects with filter", filter=compiled_filters)
        existing_models = model.objects.filter(compiled_filters)
        if not existing_models.exists():
            return CreateOperation(self, model, resource)
        return UpdateOperation(self, model, resource, existing_models)

    # pylint: disable=redefined-builtin
    def _compile_filter(self, resource: BlueprintResource, filter: BlueprintFilter) -> Q:
        """Compile a single filter"""
        if filter.type == "query":
            attribute = template_if_required(filter.attribute, **self._template_context)
            value = template_if_required(filter.value, **self._template_context)
            query = Q(**{attribute: value})
        elif filter.type == "and":
            child_filters = Q()
            for child in filter.children:
                child_filters &= self._compile_filter(resource, child)
            return child_filters
        elif filter.type == "or":
            child_filters = Q()
            for child in filter.children:
                child_filters |= self._compile_filter(resource, child)
            return child_filters
        else:
            raise ValueError(f"Invalid filter type {filter.type}")
        return query
