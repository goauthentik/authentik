from django.db.models import Model
from dramatiq.actor import Actor
from dramatiq.results.errors import ResultError
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.fields import BooleanField, CharField, ChoiceField
from rest_framework.request import Request
from rest_framework.response import Response

from authentik.api.validation import validate
from authentik.core.api.utils import ModelSerializer, PassiveSerializer
from authentik.core.models import Group, User
from authentik.events.logs import LogEventSerializer
from authentik.lib.sync.api import SyncSerializer
from authentik.lib.sync.outgoing.models import OutgoingSyncProvider, ProviderSync
from authentik.lib.utils.reflection import class_to_path, path_to_class
from authentik.rbac.filters import ObjectFilter
from authentik.tasks.models import Task


class SyncObjectSerializer(PassiveSerializer):
    """Sync object serializer"""

    sync_object_model = ChoiceField(
        choices=(
            (class_to_path(User), "user"),
            (class_to_path(Group), "group"),
        )
    )
    sync_object_id = CharField()
    override_dry_run = BooleanField(default=False)


class SyncObjectResultSerializer(PassiveSerializer):
    """Result of a single object sync"""

    messages = LogEventSerializer(many=True, read_only=True)


class ProviderSyncSerializer(SyncSerializer):
    class Meta:
        model = ProviderSync
        fields = SyncSerializer.Meta.fields + [
            "provider",
            "users_count",
            "groups_count",
            "partial",
        ]


class OutgoingSyncProviderMixin:
    """Common API Endpoints for Outgoing sync providers"""

    sync_task: Actor
    sync_objects_task: Actor
    sync_serializer: ProviderSyncSerializer

    def _syncs(self) -> Response:
        """Get provider's sync status"""
        provider: OutgoingSyncProvider = self.get_object()

        syncs = getattr(provider, f"{provider.sync_model._meta.model_name}_set").order_by(
            "-started_at"
        )

        page = self.paginate_queryset(syncs)
        if page is not None:
            serializer = self.sync_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        return Response(self.sync_serializer(syncs, many=True).data)

    @extend_schema(
        request=SyncObjectSerializer,
        responses={200: SyncObjectResultSerializer()},
    )
    @action(
        methods=["POST"],
        detail=True,
        pagination_class=None,
        url_path="sync/object",
        filter_backends=[ObjectFilter],
    )
    @validate(SyncObjectSerializer)
    def sync_object(self, request: Request, body: SyncObjectSerializer, pk: int) -> Response:
        """Sync/Re-sync a single user/group object"""
        provider = self.get_object()
        object_type = body.validated_data["sync_object_model"]
        _object_type: type[Model] = path_to_class(object_type)
        pk = body.validated_data["sync_object_id"]
        msg = self.sync_objects_task.send_with_options(
            kwargs={
                "object_type": object_type,
                "page": 1,
                "provider_pk": provider.pk,
                "override_dry_run": body.validated_data["override_dry_run"],
                "pk": pk,
            },
            retries=0,
            rel_obj=provider,
            uid=f"{provider.name}:{_object_type._meta.model_name}:{pk}:manual",
        )
        try:
            msg.get_result(block=True)
        except ResultError:
            pass
        task: Task = msg.options["task"]
        task.refresh_from_db()
        return Response(SyncObjectResultSerializer(instance={"messages": task._messages}).data)


class OutgoingSyncConnectionCreateMixin:
    """Mixin for connection objects that fetches remote data upon creation"""

    def perform_create(self, serializer: ModelSerializer):
        super().perform_create(serializer)
        try:
            instance = serializer.instance
            client = instance.provider.client_for_model(instance.__class__)
            client.update_single_attribute(instance)
            instance.save()
        except NotImplementedError:
            pass
