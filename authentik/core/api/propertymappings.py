"""PropertyMapping API Views"""
from django.shortcuts import reverse
from drf_yasg2.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework.viewsets import ReadOnlyModelViewSet

from authentik.core.api.utils import MetaNameSerializer, TypeCreateSerializer
from authentik.core.models import PropertyMapping
from authentik.lib.templatetags.authentik_utils import verbose_name
from authentik.lib.utils.reflection import all_subclasses


class PropertyMappingSerializer(ModelSerializer, MetaNameSerializer):
    """PropertyMapping Serializer"""

    object_type = SerializerMethodField(method_name="get_type")

    def get_type(self, obj):
        """Get object type so that we know which API Endpoint to use to get the full object"""
        return obj._meta.object_name.lower().replace("propertymapping", "")

    def to_representation(self, instance: PropertyMapping):
        # pyright: reportGeneralTypeIssues=false
        if instance.__class__ == PropertyMapping:
            return super().to_representation(instance)
        return instance.serializer(instance=instance).data

    class Meta:

        model = PropertyMapping
        fields = [
            "pk",
            "name",
            "expression",
            "object_type",
            "verbose_name",
            "verbose_name_plural",
        ]


class PropertyMappingViewSet(ReadOnlyModelViewSet):
    """PropertyMapping Viewset"""

    queryset = PropertyMapping.objects.none()
    serializer_class = PropertyMappingSerializer
    search_fields = [
        "name",
    ]
    filterset_fields = {"managed": ["isnull"]}
    ordering = ["name"]

    def get_queryset(self):
        return PropertyMapping.objects.select_subclasses()

    @swagger_auto_schema(responses={200: TypeCreateSerializer(many=True)})
    @action(detail=False)
    def types(self, request: Request) -> Response:
        """Get all creatable property-mapping types"""
        data = []
        for subclass in all_subclasses(self.queryset.model):
            data.append(
                {
                    "name": verbose_name(subclass),
                    "description": subclass.__doc__,
                    "link": reverse("authentik_admin:property-mapping-create")
                    + f"?type={subclass.__name__}",
                }
            )
        return Response(TypeCreateSerializer(data, many=True).data)
