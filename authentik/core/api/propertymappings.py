"""PropertyMapping API Views"""
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework.viewsets import ReadOnlyModelViewSet

from authentik.core.api.utils import MetaNameSerializer
from authentik.core.models import PropertyMapping


class PropertyMappingSerializer(ModelSerializer, MetaNameSerializer):
    """PropertyMapping Serializer"""

    object_type = SerializerMethodField(method_name="get_type")

    def get_type(self, obj):
        """Get object type so that we know which API Endpoint to use to get the full object"""
        return obj._meta.object_name.lower().replace("propertymapping", "")

    def to_representation(self, instance: PropertyMapping):
        # pyright: reportGeneralTypeIssues=false
        if instance.__class__ == PropertyMapping:
            return super().to_representation(instance)
        return instance.serializer(instance=instance).data

    class Meta:

        model = PropertyMapping
        fields = [
            "pk",
            "name",
            "expression",
            "object_type",
            "verbose_name",
            "verbose_name_plural",
        ]


class PropertyMappingViewSet(ReadOnlyModelViewSet):
    """PropertyMapping Viewset"""

    queryset = PropertyMapping.objects.none()
    serializer_class = PropertyMappingSerializer
    search_fields = [
        "name",
    ]
    filterset_fields = ["managed"]
    ordering = ["name"]

    def get_queryset(self):
        return PropertyMapping.objects.select_subclasses()
