"""Error Response schema, from https://github.com/axnsan12/drf-yasg/issues/224"""

from collections.abc import Callable
from typing import Any

from drf_spectacular.contrib.django_filters import (
    DjangoFilterExtension as BaseDjangoFilterExtension,
)
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.plumbing import (
    ResolvedComponent,
    follow_field_source,
)
from drf_spectacular.renderers import OpenApiJsonRenderer
from drf_spectacular.settings import spectacular_settings
from structlog.stdlib import get_logger

from authentik.api.apps import AuthentikAPIConfig

LOGGER = get_logger()


def preprocess_schema_exclude_non_api(endpoints: list[tuple[str, Any, Any, Callable]], **kwargs):
    """Filter out all API Views which are not mounted under /api"""
    return [
        (path, path_regex, method, callback)
        for path, path_regex, method, callback in endpoints
        if path.startswith("/" + AuthentikAPIConfig.mountpoint)
    ]


def postprocess_schema_remove_unused(
    result: dict[str, Any], generator: SchemaGenerator, **kwargs
) -> dict[str, Any]:
    """Remove unused components"""
    # To check if the schema is used, render it to JSON and then substring check that
    # less efficient than walking through the tree but a lot simpler and no
    # possibility that we miss something
    raw = OpenApiJsonRenderer().render(result, renderer_context={}).decode()
    count = 0
    for key in result["components"][ResolvedComponent.SCHEMA].keys():
        schema_usages = raw.count(f"#/components/{ResolvedComponent.SCHEMA}/{key}")
        if schema_usages >= 1:
            continue
        del generator.registry[(key, ResolvedComponent.SCHEMA)]
        count += 1
    LOGGER.debug("Removing unused components", count=count)
    result["components"] = generator.registry.build(spectacular_settings.APPEND_COMPONENTS)
    return result


class DjangoFilterExtension(BaseDjangoFilterExtension):
    """
    From https://github.com/netbox-community/netbox/pull/21521:

    Overrides drf-spectacular's DjangoFilterExtension to fix a regression in v0.29.0 where
    _get_model_field() incorrectly double-appends to_field_name when field_name already ends
    with that value (e.g. field_name='tags__slug', to_field_name='slug' produces the invalid
    path ['tags', 'slug', 'slug']). This caused hundreds of spurious warnings during schema
    generation for filters such as TagFilter, TenancyFilterSet.tenant, and OwnerFilterMixin.owner.

    See: https://github.com/netbox-community/netbox/issues/20787
         https://github.com/tfranzel/drf-spectacular/issues/1475
    """

    priority = 1

    def _get_model_field(self, filter_field, model):
        if not filter_field.field_name:
            return None
        path = filter_field.field_name.split("__")
        to_field_name = filter_field.extra.get("to_field_name")
        if to_field_name is not None and path[-1] != to_field_name:
            path.append(to_field_name)
        return follow_field_source(model, path, emit_warnings=False)
