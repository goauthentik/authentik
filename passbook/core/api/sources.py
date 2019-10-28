"""Source API Views"""
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework.viewsets import ReadOnlyModelViewSet

from passbook.admin.forms.source import SOURCE_SERIALIZER_FIELDS
from passbook.core.models import Source


class SourceSerializer(ModelSerializer):
    """Source Serializer"""

    __type__ = SerializerMethodField(method_name='get_type')

    def get_type(self, obj):
        """Get object type so that we know which API Endpoint to use to get the full object"""
        return obj._meta.object_name.lower().replace('source', '')

    class Meta:

        model = Source
        fields = SOURCE_SERIALIZER_FIELDS + ['__type__']


class SourceViewSet(ReadOnlyModelViewSet):
    """Source Viewset"""

    queryset = Source.objects.all()
    serializer_class = SourceSerializer

    def get_queryset(self):
        return Source.objects.select_subclasses()
