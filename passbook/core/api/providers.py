"""Provider API Views"""
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework.viewsets import ReadOnlyModelViewSet

from passbook.core.models import Provider


class ProviderSerializer(ModelSerializer):
    """Provider Serializer"""

    __type__ = SerializerMethodField(method_name="get_type")

    def get_type(self, obj):
        """Get object type so that we know which API Endpoint to use to get the full object"""
        return obj._meta.object_name.lower().replace("provider", "")

    class Meta:

        model = Provider
        fields = ["pk", "property_mappings", "__type__"]


class ProviderViewSet(ReadOnlyModelViewSet):
    """Provider Viewset"""

    queryset = Provider.objects.all()
    serializer_class = ProviderSerializer

    def get_queryset(self):
        return Provider.objects.select_subclasses()
