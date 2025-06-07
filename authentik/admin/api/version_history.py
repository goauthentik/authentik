from rest_framework.permissions import IsAdminUser
from rest_framework.viewsets import ReadOnlyModelViewSet

from authentik.admin.models import VersionHistory
from authentik.core.api.utils import ModelSerializer


class VersionHistorySerializer(ModelSerializer):
    """VersionHistory Serializer"""

    class Meta:
        model = VersionHistory
        fields = [
            "id",
            "timestamp",
            "version",
            "build",
        ]


class VersionHistoryViewSet(ReadOnlyModelViewSet):
    """VersionHistory Viewset"""

    queryset = VersionHistory.objects.all()
    serializer_class = VersionHistorySerializer
    permission_classes = [IsAdminUser]
    filterset_fields = [
        "version",
        "build",
    ]
    search_fields = ["version", "build"]
    ordering = ["-timestamp"]
    pagination_class = None
