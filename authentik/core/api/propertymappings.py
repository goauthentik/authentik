"""PropertyMapping API Views"""
from json import dumps

from drf_yasg.utils import swagger_auto_schema
from guardian.shortcuts import get_objects_for_user
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.fields import BooleanField, CharField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework.viewsets import GenericViewSet

from authentik.api.decorators import permission_required
from authentik.core.api.utils import (
    MetaNameSerializer,
    PassiveSerializer,
    TypeCreateSerializer,
)
from authentik.core.expression import PropertyMappingEvaluator
from authentik.core.models import PropertyMapping
from authentik.lib.templatetags.authentik_utils import verbose_name
from authentik.lib.utils.reflection import all_subclasses
from authentik.managed.api import ManagedSerializer
from authentik.policies.api.exec import PolicyTestSerializer


class PropertyMappingTestResultSerializer(PassiveSerializer):
    """Result of a Property-mapping test"""

    result = CharField(read_only=True)
    successful = BooleanField(read_only=True)


class PropertyMappingSerializer(ManagedSerializer, ModelSerializer, MetaNameSerializer):
    """PropertyMapping Serializer"""

    object_type = SerializerMethodField()

    def get_object_type(self, obj: PropertyMapping) -> str:
        """Get object type so that we know which API Endpoint to use to get the full object"""
        return obj._meta.object_name.lower().replace("propertymapping", "")

    def validate_expression(self, expression: str) -> str:
        """Test Syntax"""
        evaluator = PropertyMappingEvaluator()
        evaluator.validate(expression)
        return expression

    class Meta:

        model = PropertyMapping
        fields = [
            "pk",
            "managed",
            "name",
            "expression",
            "object_type",
            "verbose_name",
            "verbose_name_plural",
        ]


class PropertyMappingViewSet(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
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
                    "link": subclass.component,
                }
            )
        return Response(TypeCreateSerializer(data, many=True).data)

    @permission_required("authentik_core.view_propertymapping")
    @swagger_auto_schema(
        request_body=PolicyTestSerializer(),
        responses={200: PropertyMappingTestResultSerializer},
    )
    @action(detail=True, methods=["POST"])
    # pylint: disable=unused-argument, invalid-name
    def test(self, request: Request, pk: str) -> Response:
        """Test Property Mapping"""
        mapping: PropertyMapping = self.get_object()
        test_params = PolicyTestSerializer(data=request.data)
        if not test_params.is_valid():
            return Response(test_params.errors, status=400)

        # User permission check, only allow mapping testing for users that are readable
        users = get_objects_for_user(request.user, "authentik_core.view_user").filter(
            pk=test_params.validated_data["user"].pk
        )
        if not users.exists():
            raise PermissionDenied()

        response_data = {"successful": True, "result": ""}
        try:
            result = mapping.evaluate(
                users.first(),
                self.request,
                **test_params.validated_data.get("context", {}),
            )
            response_data["result"] = dumps(result)
        except Exception as exc:  # pylint: disable=broad-except
            response_data["result"] = str(exc)
            response_data["successful"] = False
        response = PropertyMappingTestResultSerializer(response_data)
        return Response(response.data)
