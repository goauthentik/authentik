"""Provider API Views"""
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.utils import MetaNameSerializer
from authentik.core.models import Provider


class ProviderSerializer(ModelSerializer, MetaNameSerializer):
    """Provider Serializer"""

    object_type = SerializerMethodField()

    def get_object_type(self, obj):
        """Get object type so that we know which API Endpoint to use to get the full object"""
        return obj._meta.object_name.lower().replace("provider", "")

    def to_representation(self, instance: Provider):
        # pyright: reportGeneralTypeIssues=false
        if instance.__class__ == Provider:
            return super().to_representation(instance)
        return instance.serializer(instance=instance).data

    class Meta:

        model = Provider
        fields = [
            "pk",
            "name",
            "application",
            "authorization_flow",
            "property_mappings",
            "object_type",
            "verbose_name",
            "verbose_name_plural",
        ]


class ProviderViewSet(ModelViewSet):
    """Provider Viewset"""

    queryset = Provider.objects.none()
    serializer_class = ProviderSerializer
    filterset_fields = {
        "application": ["isnull"],
    }
    search_fields = [
        "name",
        "application__name",
    ]

    def get_queryset(self):
        return Provider.objects.select_subclasses()
