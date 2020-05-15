"""Inlet API Views"""
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework.viewsets import ReadOnlyModelViewSet

from passbook.admin.forms.inlet import INLET_SERIALIZER_FIELDS
from passbook.core.models import Inlet


class InletSerializer(ModelSerializer):
    """Inlet Serializer"""

    __type__ = SerializerMethodField(method_name="get_type")

    def get_type(self, obj):
        """Get object type so that we know which API Endpoint to use to get the full object"""
        return obj._meta.object_name.lower().replace("inlet", "")

    class Meta:

        model = Inlet
        fields = INLET_SERIALIZER_FIELDS + ["__type__"]


class InletViewSet(ReadOnlyModelViewSet):
    """Inlet Viewset"""

    queryset = Inlet.objects.all()
    serializer_class = InletSerializer

    def get_queryset(self):
        return Inlet.objects.select_subclasses()
