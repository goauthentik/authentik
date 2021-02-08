"""Source API Views"""
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework.viewsets import ReadOnlyModelViewSet

from authentik.core.api.utils import MetaNameSerializer
from authentik.core.models import Source


class SourceSerializer(ModelSerializer, MetaNameSerializer):
    """Source Serializer"""

    object_type = SerializerMethodField()

    def get_object_type(self, obj):
        """Get object type so that we know which API Endpoint to use to get the full object"""
        return obj._meta.object_name.lower().replace("provider", "")

    class Meta:

        model = Source
        fields = SOURCE_SERIALIZER_FIELDS = [
            "pk",
            "name",
            "slug",
            "enabled",
            "authentication_flow",
            "enrollment_flow",
            "object_type",
            "verbose_name",
            "verbose_name_plural",
        ]


class SourceViewSet(ReadOnlyModelViewSet):
    """Source Viewset"""

    queryset = Source.objects.none()
    serializer_class = SourceSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return Source.objects.select_subclasses()
