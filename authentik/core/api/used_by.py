"""used_by mixin"""
from enum import Enum
from inspect import getmembers

from django.db.models.base import Model
from django.db.models.deletion import SET_DEFAULT, SET_NULL
from django.db.models.manager import Manager
from drf_spectacular.utils import extend_schema
from guardian.shortcuts import get_objects_for_user
from rest_framework.decorators import action
from rest_framework.fields import CharField, ChoiceField
from rest_framework.request import Request
from rest_framework.response import Response

from authentik.core.api.utils import PassiveSerializer


class DeleteAction(Enum):
    """Which action a delete will have on a used object"""

    CASCADE = "cascade"
    CASCADE_MANY = "cascade_many"
    SET_NULL = "set_null"
    SET_DEFAULT = "set_default"


class UsedBySerializer(PassiveSerializer):
    """A list of all objects referencing the queried object"""

    app = CharField()
    model_name = CharField()
    pk = CharField()
    name = CharField()
    action = ChoiceField(choices=[(x.name, x.name) for x in DeleteAction])


def get_delete_action(manager: Manager) -> str:
    """Get the delete action from the Foreign key, falls back to cascade"""
    if hasattr(manager, "field"):
        if manager.field.remote_field.on_delete.__name__ == SET_NULL.__name__:
            return DeleteAction.SET_NULL.name
        if manager.field.remote_field.on_delete.__name__ == SET_DEFAULT.__name__:
            return DeleteAction.SET_DEFAULT.name
    if hasattr(manager, "source_field"):
        return DeleteAction.CASCADE_MANY.name
    return DeleteAction.CASCADE.name


class UsedByMixin:
    """Mixin to add a used_by endpoint to return a list of all objects using this object"""

    @extend_schema(
        responses={200: UsedBySerializer(many=True)},
    )
    @action(detail=True, pagination_class=None, filter_backends=[])
    # pylint: disable=too-many-locals
    def used_by(self, request: Request, *args, **kwargs) -> Response:
        """Get a list of all objects that use this object"""
        model: Model = self.get_object()
        used_by = []
        shadows = []
        for attr_name, manager in getmembers(model, lambda x: isinstance(x, Manager)):
            if attr_name == "objects":  # pragma: no cover
                continue
            manager: Manager
            if manager.model._meta.abstract:
                continue
            app = manager.model._meta.app_label
            model_name = manager.model._meta.model_name
            delete_action = get_delete_action(manager)

            # To make sure we only apply shadows when there are any objects,
            # but so we only apply them once, have a simple flag for the first object
            first_object = True

            for obj in get_objects_for_user(
                request.user, f"{app}.view_{model_name}", manager
            ).all():
                # Only merge shadows on first object
                if first_object:
                    shadows += getattr(manager.model._meta, "authentik_used_by_shadows", [])
                first_object = False
                serializer = UsedBySerializer(
                    data={
                        "app": app,
                        "model_name": model_name,
                        "pk": str(obj.pk),
                        "name": str(obj),
                        "action": delete_action,
                    }
                )
                serializer.is_valid()
                used_by.append(serializer.data)
        # Check the shadows map and remove anything that should be shadowed
        for idx, user in enumerate(used_by):
            full_model_name = f"{user['app']}.{user['model_name']}"
            if full_model_name in shadows:
                del used_by[idx]
        return Response(used_by)
