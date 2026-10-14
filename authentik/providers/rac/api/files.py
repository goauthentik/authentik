"""Session-bound directory listing for the redirected RDP drive."""

from asgiref.sync import async_to_sync
from channels.exceptions import ChannelFull
from django.core.cache import cache
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from authentik.providers.rac.api.transfers import identity_for, session_active
from authentik.providers.rac.control import StreamRPC, connection_key
from authentik.providers.rac.protocol import MAX_FILE_PATH, valid_file_path


class FileListQuerySerializer(serializers.Serializer):
    """One page of the connection's redirected RDP drive."""

    token = serializers.CharField(max_length=512)
    connection = serializers.UUIDField()
    path = serializers.CharField(max_length=MAX_FILE_PATH, trim_whitespace=False)
    cursor = serializers.CharField(max_length=MAX_FILE_PATH, required=False)

    def validate_path(self, value: str) -> str:
        if not valid_file_path(value):
            raise serializers.ValidationError("Invalid virtual drive path")
        return value

    def validate_cursor(self, value: str) -> str:
        if not value or "/" in value or "\\" in value or not valid_file_path("/" + value):
            raise serializers.ValidationError("Invalid directory cursor")
        return value


class FileListEntrySerializer(serializers.Serializer):
    name = serializers.CharField()
    path = serializers.CharField()
    kind = serializers.ChoiceField(choices=["file", "directory"])
    size = serializers.IntegerField(allow_null=True)


class FileListResultSerializer(serializers.Serializer):
    entries = FileListEntrySerializer(many=True)
    cursor = serializers.CharField(allow_blank=True)


async def query_directory(identity: dict, data: dict) -> dict:
    connection = str(data["connection"])
    record = await cache.aget(connection_key(identity["tenant"], data["token"], connection))
    if not record or any(record.get(key) != value for key, value in identity.items()):
        return {"status": 404}
    if record.get("protocol") != "rdp" or not record.get("drive") or not record.get("outpost_user"):
        return {"status": 404}
    rpc = StreamRPC(
        record["channel"],
        {**identity, "token": data["token"], "connection": connection},
        timeout=10,
    )
    try:
        return await rpc.call("list", path=data["path"], cursor=data.get("cursor", ""))
    except TimeoutError, OSError, ChannelFull:
        return {"status": 503}
    finally:
        await rpc.close()


class ConnectionFileViewSet(ViewSet):
    """List only the authenticated connection's redirected RDP drive."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="rac_files_list_create",
        request=FileListQuerySerializer,
        responses=FileListResultSerializer,
    )
    @action(detail=False, methods=["POST"], url_path="list")
    def list_files(self, request):
        query = FileListQuerySerializer(data=request.data)
        query.is_valid(raise_exception=True)
        if not session_active(request):
            return Response(status=404)
        result = async_to_sync(query_directory)(
            identity_for(request),
            query.validated_data,
        )
        return Response(
            {"entries": result.get("entries", []), "cursor": result.get("cursor", "")},
            status=result["status"],
            headers={"Cache-Control": "no-store"},
        )
