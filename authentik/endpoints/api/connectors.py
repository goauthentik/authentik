from rest_framework import mixins
from rest_framework.fields import SerializerMethodField
from rest_framework.viewsets import GenericViewSet

from authentik.core.api.object_types import TypesMixin
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import MetaNameSerializer, ModelSerializer
from authentik.endpoints.models import Connector


class ConnectorSerializer(ModelSerializer, MetaNameSerializer):

    component = SerializerMethodField()

    def get_component(self, obj: Connector) -> str:  # pragma: no cover
        """Get object component so that we know how to edit the object"""
        if obj.__class__ == Connector:
            return ""
        return obj.component

    class Meta:
        model = Connector
        fields = [
            "connector_uuid",
            "name",
            "enabled",
            "component",
            "verbose_name",
            "verbose_name_plural",
            "meta_model_name",
        ]


class ConnectorViewSet(
    TypesMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """Connector Viewset"""

    queryset = Connector.objects.none()
    serializer_class = ConnectorSerializer
    search_fields = [
        "name",
    ]

    def get_queryset(self):  # pragma: no cover
        return Connector.objects.select_subclasses()
