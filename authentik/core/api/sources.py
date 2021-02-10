"""Source API Views"""
from authentik.lib.templatetags.authentik_utils import verbose_name
from authentik.lib.utils.reflection import all_subclasses
from drf_yasg2.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework.viewsets import ReadOnlyModelViewSet
from django.shortcuts import reverse
from django.utils.translation import gettext_lazy as _

from authentik.core.api.utils import MetaNameSerializer, TypeCreateSerializer
from authentik.core.models import Source


class SourceSerializer(ModelSerializer, MetaNameSerializer):
    """Source Serializer"""

    object_type = SerializerMethodField()

    def get_object_type(self, obj):
        """Get object type so that we know which API Endpoint to use to get the full object"""
        return obj._meta.object_name.lower().replace("source", "")

    class Meta:

        model = Source
        fields = SOURCE_SERIALIZER_FIELDS = [
            "pk",
            "name",
            "slug",
            "enabled",
            "authentication_flow",
            "enrollment_flow",
            "object_type",
            "verbose_name",
            "verbose_name_plural",
        ]


class SourceViewSet(ReadOnlyModelViewSet):
    """Source Viewset"""

    queryset = Source.objects.none()
    serializer_class = SourceSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return Source.objects.select_subclasses()

    @swagger_auto_schema(responses={200: TypeCreateSerializer(many=True)})
    @action(detail=False)
    # pylint: disable=unused-argument
    def types(self, request: Request) -> Response:
        """Get all creatable source types"""
        data = []
        for subclass in all_subclasses(self.queryset.model):
            data.append(
                {
                    "name": verbose_name(subclass),
                    "description": subclass.__doc__,
                    "link": reverse("authentik_admin:source-create")
                    + f"?type={subclass.__name__}",
                }
            )
        return Response(TypeCreateSerializer(data, many=True).data)
