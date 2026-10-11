from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema, extend_schema_field
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, ListField, SerializerMethodField
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer, PassiveSerializer
from authentik.rbac.endpoints import FUNCTIONS, Endpoints
from authentik.rbac.evaluator import PermissionCheckEvaluator
from authentik.rbac.models import PermissionCheck


class PermissionCheckSerializer(ModelSerializer):
    def validate_expression(self, expression: str) -> str:
        try:
            functions = PermissionCheckEvaluator.defined_functions(expression)
        except SyntaxError as exc:
            raise ValidationError(str(exc)) from None
        if not functions:
            raise ValidationError(
                _("Define at least one of {functions}.").format(functions=", ".join(FUNCTIONS))
            )
        return expression

    def validate_endpoints(self, bindings: list[str]) -> list[str]:
        for binding in bindings:
            if binding not in Endpoints.hookable():
                raise ValidationError(_("Unknown endpoint {id}.").format(id=binding))
        taken = {
            endpoint
            for check_endpoints in PermissionCheck.objects.filter(endpoints__overlap=bindings)
            .exclude(pk=getattr(self.instance, "pk", None))
            .values_list("endpoints", flat=True)
            for endpoint in check_endpoints
        }
        if overlap := taken.intersection(bindings):
            raise ValidationError(
                _("Already bound to another check: {ids}.").format(ids=", ".join(sorted(overlap)))
            )
        return bindings

    def validate(self, attrs: dict) -> dict:
        """Make sure each endpoint runs at least one function"""
        expression = attrs.get("expression", getattr(self.instance, "expression", ""))
        functions = PermissionCheckEvaluator.defined_functions(expression)
        endpoints = Endpoints.hookable()
        for binding in attrs.get("endpoints", getattr(self.instance, "endpoints", [])):
            if binding in endpoints and not functions.intersection(endpoints[binding].functions):
                raise ValidationError(
                    {"endpoints": _("{id} runs no functions defined for it.").format(id=binding)}
                )
        return attrs

    unknown_endpoints = SerializerMethodField()

    @extend_schema_field(ListField(child=CharField()))
    def get_unknown_endpoints(self, check: PermissionCheck) -> list[str]:
        """Bound endpoints that no longer exist, for example after an upgrade renamed them"""
        return [endpoint for endpoint in check.endpoints if endpoint not in Endpoints.hookable()]

    class Meta:
        model = PermissionCheck
        fields = ["pk", "name", "expression", "endpoints", "unknown_endpoints"]


class EndpointSerializer(PassiveSerializer):
    id = CharField()
    functions = ListField(child=CharField())


class PermissionCheckViewSet(UsedByMixin, ModelViewSet):
    queryset = PermissionCheck.objects.all()
    serializer_class = PermissionCheckSerializer
    search_fields = ["name", "endpoints"]
    ordering = ["name"]
    filterset_fields = ["name"]


class EndpointViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: EndpointSerializer(many=True)})
    def list(self, request: Request) -> Response:
        endpoints = sorted(Endpoints.hookable().values(), key=lambda endpoint: endpoint.id)
        return Response(EndpointSerializer(endpoints, many=True).data)
