"""PropertyMapping API Views"""
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework.viewsets import ReadOnlyModelViewSet

from authentik.core.models import PropertyMapping


class PropertyMappingSerializer(ModelSerializer):
    """PropertyMapping Serializer"""

    __type__ = SerializerMethodField(method_name="get_type")

    def get_type(self, obj):
        """Get object type so that we know which API Endpoint to use to get the full object"""
        return obj._meta.object_name.lower().replace("propertymapping", "")

    class Meta:

        model = PropertyMapping
        fields = ["pk", "name", "expression", "__type__"]


class PropertyMappingViewSet(ReadOnlyModelViewSet):
    """PropertyMapping Viewset"""

    queryset = PropertyMapping.objects.none()
    serializer_class = PropertyMappingSerializer

    def get_queryset(self):
        return PropertyMapping.objects.select_subclasses()
