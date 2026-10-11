"""used_by API"""

from enum import Enum
from inspect import getmembers

from django.apps import apps
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models.base import Model
from django.db.models.deletion import SET_DEFAULT, SET_NULL
from django.db.models.manager import Manager
from django.http import Http404
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from guardian.shortcuts import get_objects_for_user
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, ChoiceField
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from authentik.api.validation import validate
from authentik.core.api.utils import PassiveSerializer
from authentik.rbac.filters import ObjectFilter


class DeleteAction(Enum):
    """Which action a delete will have on a used object"""

    CASCADE = "cascade"
    CASCADE_MANY = "cascade_many"
    SET_NULL = "set_null"
    SET_DEFAULT = "set_default"
    LEFT_DANGLING = "left_dangling"


class UsedBySerializer(PassiveSerializer):
    """A list of all objects referencing the queried object"""

    app = CharField()
    model_name = CharField()
    pk = CharField()
    name = CharField()
    action = ChoiceField(choices=[(x.value, x.name) for x in DeleteAction])


def get_delete_action(manager: Manager) -> str:
    """Get the delete action from the Foreign key, falls back to cascade"""
    if hasattr(manager, "field"):
        if manager.field.remote_field.on_delete.__name__ == SET_NULL.__name__:
            return DeleteAction.SET_NULL.value
        if manager.field.remote_field.on_delete.__name__ == SET_DEFAULT.__name__:
            return DeleteAction.SET_DEFAULT.value
    if hasattr(manager, "source_field"):
        return DeleteAction.CASCADE_MANY.value
    return DeleteAction.CASCADE.value


class UsedByParameters(PassiveSerializer):
    """Parameters to look up which objects use a given object"""

    model = CharField(help_text="Fully qualified model name, in the form `<app_label>.<model>`")
    pk = CharField(help_text="The object's primary key, or other unique identifier it exposes")


class UsedByView(APIView):
    """Get a list of all objects that use a given object, identified by its model and pk"""

    permission_classes = [IsAuthenticated]
    # Set per-request by `get_target` based on the resolved model, and read by `ObjectFilter`
    owner_field = None

    def get_target(self, request: Request, params: dict[str, str]) -> Model:
        """Resolve the `model`/`pk` parameters to a model instance the user may view"""
        app_label, _, model_name = params["model"].partition(".")
        try:
            model = apps.get_model(app_label, model_name)
        except LookupError:
            raise ValidationError({"model": "Invalid model"}) from None
        # Models can declare `authentik_used_by_owner_field` in their Meta to allow
        # their owner to query used_by even without an explicit view permission,
        # mirroring the `owner_field` that viewsets use for the same purpose.
        self.owner_field = getattr(model._meta, "authentik_used_by_owner_field", None)
        queryset = ObjectFilter().filter_queryset(request, model.objects.all(), self)
        # Models can declare `authentik_used_by_lookup_field` in their Meta when their
        # primary key isn't safe to expose through the API (for example a session key)
        lookup_field = getattr(model._meta, "authentik_used_by_lookup_field", "pk")
        try:
            return get_object_or_404(queryset, **{lookup_field: params["pk"]})
        except DjangoValidationError:
            # The pk doesn't even have the right shape (e.g. not a UUID) for this model
            raise Http404 from None

    @extend_schema(
        parameters=[UsedByParameters],
        responses={200: UsedBySerializer(many=True)},
    )
    @validate(UsedByParameters, location="query")
    def get(self, request: Request, query: UsedByParameters) -> Response:
        """Get a list of all objects that use this object"""
        target = self.get_target(request, query.validated_data)
        used_by = []
        shadows = []
        for attr_name, manager in getmembers(target, lambda x: isinstance(x, Manager)):
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

            # TODO: This will only return the used-by references that the user can see
            # Either we have to leak model information here to not make the list
            # useless if the user doesn't have all permissions, or we need to double
            # query and check if there is a difference between modes the user can see
            # and can't see and add a warning
            for obj in get_objects_for_user(
                request.user, f"{app}.view_{model_name}", manager.all()
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
