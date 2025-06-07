"""API Utilities"""

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.fields import (
    BooleanField,
    CharField,
)
from rest_framework.request import Request
from rest_framework.response import Response

from authentik.core.api.utils import PassiveSerializer
from authentik.enterprise.apps import EnterpriseConfig
from authentik.lib.utils.reflection import all_subclasses


class TypeCreateSerializer(PassiveSerializer):
    """Types of an object that can be created"""

    name = CharField(required=True)
    description = CharField(required=True)
    component = CharField(required=True)
    model_name = CharField(required=True)

    icon_url = CharField(required=False)
    requires_enterprise = BooleanField(default=False)


class CreatableType:
    """Class to inherit from to mark a model as creatable, even if the model itself is marked
    as abstract"""


class NonCreatableType:
    """Class to inherit from to mark a model as non-creatable even if it is not abstract"""


class TypesMixin:
    """Mixin which adds an API endpoint to list all possible types that can be created"""

    @extend_schema(responses={200: TypeCreateSerializer(many=True)})
    @action(detail=False, pagination_class=None, filter_backends=[])
    def types(self, request: Request, additional: list[dict] | None = None) -> Response:
        """Get all creatable types"""
        data = []
        for subclass in all_subclasses(self.queryset.model):
            instance = None
            if subclass._meta.abstract:
                if not issubclass(subclass, CreatableType):
                    continue
                # Circumvent the django protection for not being able to instantiate
                # abstract models. We need a model instance to access .component
                # and further down .icon_url
                instance = subclass.__new__(subclass)
                # Django re-sets abstract = False so we need to override that
                instance.Meta.abstract = True
            else:
                if issubclass(subclass, NonCreatableType):
                    continue
                instance = subclass()
            try:
                data.append(
                    {
                        "name": subclass._meta.verbose_name,
                        "description": subclass.__doc__,
                        "component": instance.component,
                        "model_name": subclass._meta.model_name,
                        "icon_url": getattr(instance, "icon_url", None),
                        "requires_enterprise": isinstance(
                            subclass._meta.app_config, EnterpriseConfig
                        ),
                    }
                )
            except NotImplementedError:
                continue
        if additional:
            data.extend(additional)
        data = sorted(data, key=lambda x: x["name"])
        return Response(TypeCreateSerializer(data, many=True).data)
