"""used_by mixin"""
from inspect import getmembers

from django.db.models.base import Model
from django.db.models.manager import Manager
from drf_spectacular.utils import extend_schema
from guardian.shortcuts import get_objects_for_user
from rest_framework.decorators import action
from rest_framework.fields import CharField
from rest_framework.request import Request
from rest_framework.response import Response

from authentik.core.api.utils import PassiveSerializer


class UsedBySerializer(PassiveSerializer):
    """A list of all objects referencing the queried object"""

    app = CharField()
    model_name = CharField()
    pk = CharField()
    name = CharField()


class UsedByMixin:
    """Mixin to add a used_by endpoint to return a list of all objects using this object"""

    @extend_schema(
        responses={200: UsedBySerializer(many=True)},
    )
    @action(detail=True, pagination_class=None, filter_backends=[])
    # pylint: disable=invalid-name, unused-argument, too-many-locals
    def used_by(self, request: Request, pk: str) -> Response:
        """Get a list of all objects that use this object"""
        # pyright: reportGeneralTypeIssues=false
        certificate: Model = self.get_object()
        used_by = []
        shadows = []
        for attr_name, manager in getmembers(
            certificate, lambda x: isinstance(x, Manager)
        ):
            if attr_name == "objects":  # pragma: no cover
                continue
            manager: Manager
            if manager.model._meta.abstract:
                continue
            shadows += getattr(manager.model._meta, "authentik_used_by_shadows", [])
            app = manager.model._meta.app_label
            model_name = manager.model._meta.model_name
            perm = f"{app}.view_{model_name}"
            for obj in get_objects_for_user(request.user, perm, manager).all():
                serializer = UsedBySerializer(
                    data={
                        "app": app,
                        "model_name": model_name,
                        "pk": str(obj.pk),
                        "name": str(obj),
                    }
                )
                serializer.is_valid()
                used_by.append(serializer.data)
        # Check the shadows map and remove anything that should be shadowed
        for idx, user in enumerate(used_by):
            fqmn = f"{user['app']}.{user['model_name']}"
            if fqmn in shadows:
                del used_by[idx]
        return Response(used_by)
