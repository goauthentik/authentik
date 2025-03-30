from typing import Any

from django.http import HttpRequest
from structlog.stdlib import get_logger

from authentik.common.sync.mapper import PropertyMappingManager
from authentik.core.expression.exceptions import PropertyMappingExpressionException
from authentik.core.models import Group, PropertyMapping, Source, User
from authentik.events.models import Event, EventAction
from authentik.lib.merge import MERGE_LIST_UNIQUE
from authentik.policies.utils import delete_none_values

LOGGER = get_logger()


class SourceMapper:
    def __init__(self, source: Source):
        self.source = source

    def get_manager(
        self, object_type: type[User | Group], context_keys: list[str]
    ) -> PropertyMappingManager:
        """Get property mapping manager for this source."""

        qs = PropertyMapping.objects.none()
        if object_type == User:
            qs = self.source.user_property_mappings.all().select_subclasses()
        elif object_type == Group:
            qs = self.source.group_property_mappings.all().select_subclasses()
        qs = qs.order_by("name")
        return PropertyMappingManager(
            qs,
            self.source.property_mapping_type,
            ["source", "properties"] + context_keys,
        )

    def get_base_properties(
        self, object_type: type[User | Group], **kwargs
    ) -> dict[str, Any | dict[str, Any]]:
        """Get base properties for a user or a group to build final properties upon."""
        if object_type == User:
            properties = self.source.get_base_user_properties(**kwargs)
            properties.setdefault("path", self.source.get_user_path())
            return properties
        if object_type == Group:
            return self.source.get_base_group_properties(**kwargs)
        return {}

    def build_object_properties(
        self,
        object_type: type[User | Group],
        manager: "PropertyMappingManager | None" = None,
        user: User | None = None,
        request: HttpRequest | None = None,
        **kwargs,
    ) -> dict[str, Any | dict[str, Any]]:
        """Build a user or group properties from the source configured property mappings."""

        properties = self.get_base_properties(object_type, **kwargs)
        if "attributes" not in properties:
            properties["attributes"] = {}

        if not manager:
            manager = self.get_manager(object_type, list(kwargs.keys()))
        evaluations = manager.iter_eval(
            user=user,
            request=request,
            return_mapping=True,
            source=self.source,
            properties=properties,
            **kwargs,
        )
        while True:
            try:
                value, mapping = next(evaluations)
            except StopIteration:
                break
            except PropertyMappingExpressionException as exc:
                Event.new(
                    EventAction.CONFIGURATION_ERROR,
                    message=f"Failed to evaluate property mapping: '{exc.mapping.name}'",
                    source=self,
                    mapping=exc.mapping,
                ).save()
                LOGGER.warning(
                    "Mapping failed to evaluate",
                    exc=exc,
                    source=self,
                    mapping=exc.mapping,
                )
                raise exc

            if not value or not isinstance(value, dict):
                LOGGER.debug(
                    "Mapping evaluated to None or is not a dict. Skipping",
                    source=self,
                    mapping=mapping,
                )
                continue

            MERGE_LIST_UNIQUE.merge(properties, value)

        return delete_none_values(properties)
