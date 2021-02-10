"""Provider API Views"""
from django.shortcuts import reverse
from django.utils.translation import gettext_lazy as _
from drf_yasg2.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.fields import ReadOnlyField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework.viewsets import ModelViewSet

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
            "application",
            "authorization_flow",
            "property_mappings",
            "object_type",
            "assigned_application_slug",
            "assigned_application_name",
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

    @swagger_auto_schema(responses={200: TypeCreateSerializer(many=True)})
    @action(detail=False)
    # pylint: disable=unused-argument
    def types(self, request: Request) -> Response:
        """Get all creatable provider types"""
        data = []
        for subclass in all_subclasses(self.queryset.model):
            data.append(
                {
                    "name": verbose_name(subclass),
                    "description": subclass.__doc__,
                    "link": reverse("authentik_admin:provider-create")
                    + f"?type={subclass.__name__}",
                }
            )
        data.append(
            {
                "name": _("SAML Provider from Metadata"),
                "description": _("Create a SAML Provider by importing its Metadata."),
                "link": reverse("authentik_admin:provider-saml-from-metadata"),
            }
        )
        return Response(TypeCreateSerializer(data, many=True).data)
