"""Session-bound control API for redirected RDP drive transfers."""

from sys import maxsize
from uuid import UUID, uuid4

from asgiref.sync import async_to_sync
from channels.exceptions import ChannelFull
from django.core.cache import cache
from django.db import connection
from django.db.models import Q
from django.utils.timezone import now
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from authentik.core.models import AuthenticatedSession
from authentik.providers.rac.control import StreamRPC, connection_key
from authentik.providers.rac.protocol import MAX_FILE_PATH, valid_file_path


def transfer_key(identifier: str) -> str:
    return f"rac-bulk/{identifier}"


class TransferCreateSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=512)
    connection = serializers.UUIDField()
    direction = serializers.ChoiceField(choices=["upload", "download"])
    path = serializers.CharField(max_length=MAX_FILE_PATH, trim_whitespace=False)
    size = serializers.IntegerField(min_value=0, max_value=maxsize, required=False)

    def validate(self, attrs: dict) -> dict:
        if not valid_file_path(attrs["path"]) or attrs["path"] == "/":
            raise serializers.ValidationError("Invalid virtual drive path")
        if attrs["direction"] == "upload" and "size" not in attrs:
            raise serializers.ValidationError("Upload size is required")
        return attrs


class TransferSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    filename = serializers.CharField()
    size = serializers.IntegerField()


class TransferActionSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=512)
    connection = serializers.UUIDField()


def session_active(request) -> bool:
    return bool(
        request.session.session_key
        and AuthenticatedSession.objects.filter(
            Q(session__expiring=False) | Q(session__expires__gt=now()),
            user=request.user,
            user__is_active=True,
            session__session_key=request.session.session_key,
        ).exists()
    )


def identity_for(request) -> dict:
    return {
        "user": str(request.user.pk),
        "session": request.session.session_key,
        "tenant": connection.schema_name,
    }


def connection_record(identity: dict, token: str, connection: UUID) -> dict | None:
    record = cache.get(connection_key(identity["tenant"], token, str(connection)))
    if not record or any(record.get(key) != value for key, value in identity.items()):
        return None
    if record.get("protocol") != "rdp" or not record.get("drive") or not record.get("outpost_user"):
        return None
    return record


async def control(
    record: dict, identity: dict, token: str, connection: UUID, action: str, **kwargs
) -> dict:
    rpc = StreamRPC(
        record["channel"],
        {**identity, "token": token, "connection": str(connection)},
        timeout=15,
    )
    try:
        return await rpc.call(action, **kwargs)
    except TimeoutError, OSError, ChannelFull:
        return {"status": 503}
    finally:
        await rpc.close()


class FileTransferViewSet(ViewSet):
    """Prepare and finish file transfers through low-volume Outpost control messages."""

    permission_classes = [IsAuthenticated]

    @extend_schema(request=TransferCreateSerializer, responses=TransferSerializer)
    def create(self, request):
        query = TransferCreateSerializer(data=request.data)
        query.is_valid(raise_exception=True)
        if not session_active(request):
            return Response(status=404)
        data = query.validated_data
        identity = identity_for(request)
        record = connection_record(identity, data["token"], data["connection"])
        if not record:
            return Response(status=404)
        if not record.get(data["direction"]):
            return Response(status=403)
        identifier = str(uuid4())
        transfer = {
            **identity,
            "token": data["token"],
            "connection": str(data["connection"]),
            "direction": data["direction"],
            "path": data["path"],
            "size": data.get("size", 0),
            "outpost_user": record["outpost_user"],
            "channel": record["channel"],
            "owner": None,
            "prepared": False,
        }
        cache.set(transfer_key(identifier), transfer, timeout=90)
        result = async_to_sync(control)(
            record,
            identity,
            data["token"],
            data["connection"],
            "prepare",
            transfer=identifier,
            path=data["path"],
            direction=data["direction"],
            size=data.get("size", 0),
        )
        if result["status"] != status.HTTP_200_OK:
            cache.delete(transfer_key(identifier))
            return Response(status=result["status"])
        transfer = cache.get(transfer_key(identifier))
        if transfer is None:
            return Response(status=503)
        transfer["size"] = result["size"]
        transfer["prepared"] = True
        cache.set(transfer_key(identifier), transfer, timeout=90)
        return Response(
            {
                "id": identifier,
                "filename": data["path"].rsplit("/", 1)[-1],
                "size": transfer["size"],
            },
            status=201,
            headers={"Cache-Control": "no-store"},
        )

    def _action(self, request, pk: str, action: str):
        if not session_active(request):
            return Response(status=404)
        try:
            identifier = str(UUID(pk))
        except ValueError:
            return Response(status=404)
        identity = identity_for(request)
        transfer = cache.get(transfer_key(identifier))
        if not transfer or any(transfer.get(key) != value for key, value in identity.items()):
            return Response(status=404)
        if action == "finish":
            query = TransferActionSerializer(data=request.data)
            query.is_valid(raise_exception=True)
            if transfer["token"] != query.validated_data["token"] or transfer["connection"] != str(
                query.validated_data["connection"]
            ):
                return Response(status=404)
        connection = UUID(transfer["connection"])
        record = connection_record(identity, transfer["token"], connection)
        if not record or record["channel"] != transfer["channel"]:
            return Response(status=404)
        result = async_to_sync(control)(
            record,
            identity,
            transfer["token"],
            connection,
            action,
            transfer=identifier,
        )
        if action == "cancel" or result["status"] == status.HTTP_200_OK:
            cache.delete(transfer_key(identifier))
            cache.delete(f"rac-bulk-owner/{identifier}")
        return Response(status=result["status"])

    @extend_schema(
        parameters=[OpenApiParameter("id", OpenApiTypes.UUID, OpenApiParameter.PATH)],
        request=TransferActionSerializer,
        responses={200: None},
    )
    @action(detail=True, methods=["POST"])
    def finish(self, request, pk=None):
        return self._action(request, pk, "finish")

    @extend_schema(
        parameters=[OpenApiParameter("id", OpenApiTypes.UUID, OpenApiParameter.PATH)],
        request=None,
        responses={200: None},
    )
    def destroy(self, request, pk=None):
        return self._action(request, pk, "cancel")
