"""Provider API Views"""
from django.utils.translation import gettext_lazy as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.fields import ReadOnlyField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework.viewsets import GenericViewSet

from authentik.core.api.utils import MetaNameSerializer, TypeCreateSerializer
from authentik.core.models import Provider
from authentik.lib.templatetags.authentik_utils import verbose_name
from authentik.lib.utils.reflection import all_subclasses


class ProviderSerializer(ModelSerializer, MetaNameSerializer):
    """Provider Serializer"""

    assigned_application_slug = ReadOnlyField(source="application.slug")
    assigned_application_name = ReadOnlyField(source="application.name")

    object_type = SerializerMethodField()

    def get_object_type(self, obj):
        """Get object type so that we know which API Endpoint to use to get the full object"""
        return obj._meta.object_name.lower().replace("provider", "")

    class Meta:

        model = Provider
        fields = [
            "pk",
            "name",
            "authorization_flow",
            "property_mappings",
            "object_type",
            "assigned_application_slug",
            "assigned_application_name",
            "verbose_name",
            "verbose_name_plural",
        ]


class ProviderViewSet(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
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

    def get_queryset(self):
        return Provider.objects.select_subclasses()

    @swagger_auto_schema(responses={200: TypeCreateSerializer(many=True)})
    @action(detail=False)
    def types(self, request: Request) -> Response:
        """Get all creatable provider types"""
        data = []
        for subclass in all_subclasses(self.queryset.model):
            data.append(
                {
                    "name": verbose_name(subclass),
                    "description": subclass.__doc__,
                    "link": subclass().component,
                }
            )
        data.append(
            {
                "name": _("SAML Provider from Metadata"),
                "description": _("Create a SAML Provider by importing its Metadata."),
                "link": "ak-provider-saml-import-form",
            }
        )
        return Response(TypeCreateSerializer(data, many=True).data)
