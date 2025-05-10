"""PropertyMapping API Views"""

from json import dumps

from django_filters.filters import AllValuesMultipleFilter, BooleanFilter
from django_filters.filterset import FilterSet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_field,
)
from guardian.shortcuts import get_objects_for_user
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.fields import BooleanField, CharField, SerializerMethodField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from authentik.blueprints.api import ManagedSerializer
from authentik.common.utils.errors import exception_to_string
from authentik.core.api.object_types import TypesMixin
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import (
    MetaNameSerializer,
    ModelSerializer,
    PassiveSerializer,
)
from authentik.core.expression.evaluator import PropertyMappingEvaluator
from authentik.core.expression.exceptions import PropertyMappingExpressionException
from authentik.core.models import Group, PropertyMapping, User
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


class PropertyMappingFilterSet(FilterSet):
    """Filter for PropertyMapping"""

    managed = extend_schema_field(OpenApiTypes.STR)(AllValuesMultipleFilter(field_name="managed"))

    managed__isnull = BooleanFilter(field_name="managed", lookup_expr="isnull")

    class Meta:
        model = PropertyMapping
        fields = ["name", "managed"]


class PropertyMappingViewSet(
    TypesMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """PropertyMapping Viewset"""

    class PropertyMappingTestSerializer(PolicyTestSerializer):
        """Test property mapping execution for a user/group with context"""

        user = PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True)
        group = PrimaryKeyRelatedField(
            queryset=Group.objects.all(), required=False, allow_null=True
        )

    queryset = PropertyMapping.objects.select_subclasses()
    serializer_class = PropertyMappingSerializer
    filterset_class = PropertyMappingFilterSet
    ordering = ["name"]
    search_fields = ["name"]

    @permission_required("authentik_core.view_propertymapping")
    @extend_schema(
        request=PropertyMappingTestSerializer(),
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
        mapping: PropertyMapping = PropertyMapping.objects.get_subclass(pk=_mapping.pk)
        # FIXME: when we separate policy mappings between ones for sources
        # and ones for providers, we need to make the user field optional for the source mapping
        test_params = self.PropertyMappingTestSerializer(data=request.data)
        if not test_params.is_valid():
            return Response(test_params.errors, status=400)

        format_result = str(request.GET.get("format_result", "false")).lower() == "true"

        context: dict = test_params.validated_data.get("context", {})
        context.setdefault("user", None)

        if user := test_params.validated_data.get("user"):
            # User permission check, only allow mapping testing for users that are readable
            users = get_objects_for_user(request.user, "authentik_core.view_user").filter(
                pk=user.pk
            )
            if not users.exists():
                raise PermissionDenied()
            context["user"] = user
        if group := test_params.validated_data.get("group"):
            # Group permission check, only allow mapping testing for groups that are readable
            groups = get_objects_for_user(request.user, "authentik_core.view_group").filter(
                pk=group.pk
            )
            if not groups.exists():
                raise PermissionDenied()
            context["group"] = group
        context["request"] = self.request

        response_data = {"successful": True, "result": ""}
        try:
            result = mapping.evaluate(dry_run=True, **context)
            response_data["result"] = dumps(
                sanitize_item(result), indent=(4 if format_result else None)
            )
        except PropertyMappingExpressionException as exc:
            response_data["result"] = exception_to_string(exc.exc)
            response_data["successful"] = False
        except Exception as exc:
            response_data["result"] = exception_to_string(exc)
            response_data["successful"] = False
        response = PropertyMappingTestResultSerializer(response_data)
        return Response(response.data)
