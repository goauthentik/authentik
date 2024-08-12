"""Expression Policy API"""

from drf_spectacular.utils import OpenApiResponse, extend_schema
from guardian.shortcuts import get_objects_for_user
from rest_framework.decorators import action
from rest_framework.fields import CharField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from structlog.stdlib import get_logger

from authentik.core.api.used_by import UsedByMixin
from authentik.events.logs import LogEventSerializer, capture_logs
from authentik.policies.api.exec import PolicyTestResultSerializer, PolicyTestSerializer
from authentik.policies.api.policies import PolicySerializer
from authentik.policies.expression.evaluator import PolicyEvaluator
from authentik.policies.expression.models import ExpressionPolicy
from authentik.policies.models import PolicyBinding
from authentik.policies.process import PolicyProcess
from authentik.policies.types import PolicyRequest
from authentik.rbac.decorators import permission_required

LOGGER = get_logger()


class ExpressionPolicySerializer(PolicySerializer):
    """Group Membership Policy Serializer"""

    def validate_expression(self, expr: str) -> str:
        """validate the syntax of the expression"""
        name = "temp-policy" if not self.instance else self.instance.name
        PolicyEvaluator(name).validate(expr)
        return expr

    class Meta:
        model = ExpressionPolicy
        fields = PolicySerializer.Meta.fields + ["expression"]


class ExpressionPolicyViewSet(UsedByMixin, ModelViewSet):
    """Source Viewset"""

    queryset = ExpressionPolicy.objects.all()
    serializer_class = ExpressionPolicySerializer
    filterset_fields = "__all__"
    ordering = ["name"]
    search_fields = ["name"]

    class ExpressionPolicyTestSerializer(PolicyTestSerializer):
        """Expression policy test serializer"""

        expression = CharField()

    @permission_required("authentik_policies.view_policy")
    @extend_schema(
        request=ExpressionPolicyTestSerializer(),
        responses={
            200: PolicyTestResultSerializer(),
            400: OpenApiResponse(description="Invalid parameters"),
        },
    )
    @action(detail=True, pagination_class=None, filter_backends=[], methods=["POST"])
    def test(self, request: Request, pk: str) -> Response:
        """Test policy"""
        policy = self.get_object()
        test_params = self.ExpressionPolicyTestSerializer(data=request.data)
        if not test_params.is_valid():
            return Response(test_params.errors, status=400)

        # User permission check, only allow policy testing for users that are readable
        users = get_objects_for_user(request.user, "authentik_core.view_user").filter(
            pk=test_params.validated_data["user"].pk
        )
        if not users.exists():
            return Response(status=400)

        policy.expression = test_params.validated_data["expression"]

        p_request = PolicyRequest(users.first())
        p_request.debug = True
        p_request.set_http_request(self.request)
        p_request.context = test_params.validated_data.get("context", {})

        proc = PolicyProcess(PolicyBinding(policy=policy), p_request, None)
        with capture_logs() as logs:
            result = proc.execute()
        log_messages = []
        for log in logs:
            if log.attributes.get("process", "") == "PolicyProcess":
                continue
            log_messages.append(LogEventSerializer(log).data)
        result.log_messages = log_messages
        response = PolicyTestResultSerializer(result)
        return Response(response.data)
