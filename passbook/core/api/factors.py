"""Factor API Views"""
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework.viewsets import ReadOnlyModelViewSet

from passbook.core.models import Factor


class FactorSerializer(ModelSerializer):
    """Factor Serializer"""

    __type__ = SerializerMethodField(method_name="get_type")

    def get_type(self, obj):
        """Get object type so that we know which API Endpoint to use to get the full object"""
        return obj._meta.object_name.lower().replace("factor", "")

    class Meta:

        model = Factor
        fields = ["pk", "name", "slug", "order", "enabled", "__type__"]


class FactorViewSet(ReadOnlyModelViewSet):
    """Factor Viewset"""

    queryset = Factor.objects.all()
    serializer_class = FactorSerializer

    def get_queryset(self):
        return Factor.objects.select_subclasses()
