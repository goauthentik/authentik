from dramatiq.actor import Actor
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.fields import BooleanField, CharField, ChoiceField
from rest_framework.request import Request
from rest_framework.response import Response

from authentik.core.api.utils import ModelSerializer, PassiveSerializer
from authentik.core.models import Group, User
from authentik.events.logs import LogEvent, LogEventSerializer
from authentik.lib.sync.outgoing.models import OutgoingSyncProvider
from authentik.lib.utils.reflection import class_to_path
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


class OutgoingSyncProviderStatusMixin:
    """Common API Endpoints for Outgoing sync providers"""

    sync_objects_task: type[Actor] = None

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
    def sync_object(self, request: Request, pk: int) -> Response:
        """Sync/Re-sync a single user/group object"""
        provider: OutgoingSyncProvider = self.get_object()
        params = SyncObjectSerializer(data=request.data)
        params.is_valid(raise_exception=True)
        msg = self.sync_objects_task.send_with_options(
            args=(params.validated_data["sync_object_model"],),
            kwargs={
                "page": 1,
                "provider_pk": provider.pk,
                "pk": params.validated_data["sync_object_id"],
                "override_dry_run": params.validated_data["override_dry_run"],
            },
            rel_obj=provider,
        )
        msg.get_result(block=True)
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
