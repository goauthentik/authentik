"""PropertyMapping API Views"""

from json import dumps

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from guardian.shortcuts import get_objects_for_user
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.fields import BooleanField, CharField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework.viewsets import GenericViewSet

from authentik.blueprints.api import ManagedSerializer
from authentik.core.api.object_types import TypesMixin
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import (
    MetaNameSerializer,
    PassiveSerializer,
)
from authentik.core.expression.evaluator import PropertyMappingEvaluator
from authentik.core.models import PropertyMapping
from authentik.events.utils import sanitize_item
from authentik.policies.api.exec import PolicyTestSerializer
from authentik.rbac.decorators import permission_required


class PropertyMappingTestResultSerializer(PassiveSerializer):
    """Result of a Property-mapping test"""

    result = CharField(read_only=True)
    successful = BooleanField(read_only=True)


class PropertyMappingSerializer(ManagedSerializer, ModelSerializer, MetaNameSerializer):
    """PropertyMapping Serializer"""

    component = SerializerMethodField()

    def get_component(self, obj: PropertyMapping) -> str:
        """Get object's component so that we know how to edit the object"""
        return obj.component

    def validate_expression(self, expression: str) -> str:
        """Test Syntax"""
        evaluator = PropertyMappingEvaluator(
            self.instance,
        )
        evaluator.validate(expression)
        return expression

    class Meta:
        model = PropertyMapping
        fields = [
            "pk",
            "managed",
            "name",
            "expression",
            "component",
            "verbose_name",
            "verbose_name_plural",
            "meta_model_name",
        ]


class PropertyMappingViewSet(
    TypesMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
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

    def get_queryset(self):  # pragma: no cover
        return PropertyMapping.objects.select_subclasses()

    @permission_required("authentik_core.view_propertymapping")
    @extend_schema(
        request=PolicyTestSerializer(),
        responses={
            200: PropertyMappingTestResultSerializer,
            400: OpenApiResponse(description="Invalid parameters"),
        },
        parameters=[
            OpenApiParameter(
                name="format_result",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.BOOL,
            )
        ],
    )
    @action(detail=True, pagination_class=None, filter_backends=[], methods=["POST"])
    def test(self, request: Request, pk: str) -> Response:
        """Test Property Mapping"""
        _mapping: PropertyMapping = self.get_object()
        # Use `get_subclass` to get correct class and correct `.evaluate` implementation
        mapping = PropertyMapping.objects.get_subclass(pk=_mapping.pk)
        # FIXME: when we separate policy mappings between ones for sources
        # and ones for providers, we need to make the user field optional for the source mapping
        test_params = PolicyTestSerializer(data=request.data)
        if not test_params.is_valid():
            return Response(test_params.errors, status=400)

        format_result = str(request.GET.get("format_result", "false")).lower() == "true"

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
            response_data["result"] = dumps(
                sanitize_item(result), indent=(4 if format_result else None)
            )
        except Exception as exc:
            response_data["result"] = str(exc)
            response_data["successful"] = False
        response = PropertyMappingTestResultSerializer(response_data)
        return Response(response.data)
