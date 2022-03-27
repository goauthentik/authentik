"""Provider API Views"""
from django.utils.translation import gettext_lazy as _
from rest_framework import mixins
from rest_framework.fields import ReadOnlyField
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework.viewsets import GenericViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import MetaNameSerializer
from authentik.core.models import Provider


class ProviderSerializer(ModelSerializer, MetaNameSerializer):
    """Provider Serializer"""

    assigned_application_slug = ReadOnlyField(source="application.slug")
    assigned_application_name = ReadOnlyField(source="application.name")

    component = SerializerMethodField()

    def get_component(self, obj: Provider) -> str:  # pragma: no cover
        """Get object component so that we know how to edit the object"""
        # pyright: reportGeneralTypeIssues=false
        if obj.__class__ == Provider:
            return ""
        return obj.component

    class Meta:

        model = Provider
        fields = [
            "pk",
            "name",
            "authorization_flow",
            "property_mappings",
            "component",
            "assigned_application_slug",
            "assigned_application_name",
            "verbose_name",
            "verbose_name_plural",
            "meta_model_name",
        ]


class ProviderViewSet(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
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

    def get_queryset(self):  # pragma: no cover
        return Provider.objects.select_subclasses()
