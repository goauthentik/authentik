"""Outlet API Views"""
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework.viewsets import ReadOnlyModelViewSet

from passbook.core.models import Outlet


class OutletSerializer(ModelSerializer):
    """Outlet Serializer"""

    __type__ = SerializerMethodField(method_name="get_type")

    def get_type(self, obj):
        """Get object type so that we know which API Endpoint to use to get the full object"""
        return obj._meta.object_name.lower().replace("outlet", "")

    class Meta:

        model = Outlet
        fields = ["pk", "property_mappings", "__type__"]


class OutletViewSet(ReadOnlyModelViewSet):
    """Outlet Viewset"""

    queryset = Outlet.objects.all()
    serializer_class = OutletSerializer

    def get_queryset(self):
        return Outlet.objects.select_subclasses()
