from http import HTTPMethod

from django.http import Http404
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_field
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.fields import BooleanField, CharField, ChoiceField, SerializerMethodField
from rest_framework.mixins import (
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from authentik.api.validation import validate
from authentik.brands.models import Brand
from authentik.core.api.groups import PartialUserSerializer
from authentik.core.api.utils import (
    JSONDictField,
    LinkSerializer,
    ModelSerializer,
    PassiveSerializer,
)
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.requests.api.apps import (
    RequestableTargetSerializer,
    granting_rule_bindings,
    user_can_request,
)
from authentik.enterprise.requests.models import (
    GrantRequest,
    RequestRule,
    RequestStatus,
)
from authentik.enterprise.requests.stage import (
    PLAN_CONTEXT_GRANT_MAX_EXPIRY,
    PLAN_CONTEXT_GRANT_PENDING_EXPIRY,
    PLAN_CONTEXT_GRANT_REQUESTED_EXPIRY,
    PLAN_CONTEXT_GRANT_REQUESTED_PBMS,
    GrantRequestFinalStageView,
)
from authentik.flows.models import Flow, in_memory_stage
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlanner
from authentik.lib.utils.time import timedelta_from_string, timedelta_string_validator
from authentik.policies.api.bindings import PolicyBindingModelForeignKey
from authentik.policies.engine import ListPolicyEngine
from authentik.policies.models import PolicyBindingModel, RequestableChildModel, RequestableModel
from authentik.rbac.decorators import permission_required


class GrantRequestSerializer(EnterpriseRequiredMixin, ModelSerializer):

    created_by = PartialUserSerializer(read_only=True)
    revoked_by = PartialUserSerializer(read_only=True)
    is_active = BooleanField(read_only=True)

    target_objs = SerializerMethodField()

    @extend_schema_field(RequestableTargetSerializer(many=True))
    def get_target_objs(self, inst: GrantRequest) -> list[RequestableTargetSerializer]:
        return RequestableTargetSerializer(inst.targets.all().select_subclasses(), many=True).data

    class Meta:
        model = GrantRequest
        fields = [
            "created",
            "created_by",
            "requester_data",
            "fulfiller_data",
            "revoked_by",
            "is_active",
            "expires",
            "status",
            "targets",
            "target_objs",
            "uuid",
        ]
        extra_kwargs = {
            "status": {"read_only": True},
        }


class GrantRequestViewSet(RetrieveModelMixin, DestroyModelMixin, ListModelMixin, GenericViewSet):

    # All requests are visible to users even if they're expired
    queryset = GrantRequest.objects.including_expired()
    serializer_class = GrantRequestSerializer
    filterset_fields = ["created_by", "status"]
    rbac_allow_create_without_perm = True

    class GrantRequestCreateSerializer(PassiveSerializer):

        pbms = PolicyBindingModelForeignKey(
            queryset=PolicyBindingModel.objects.select_subclasses(), many=True
        )
        expiry = CharField(
            required=False,
            allow_blank=True,
            validators=[timedelta_string_validator],
            help_text=(
                "Optional override for how long the grant should last once approved. "
                "Clamped to the granting rule binding(s)' expiry_granted_max."
            ),
        )

        def validate_pbms(self, pbms: list[PolicyBindingModel]) -> list[PolicyBindingModel]:
            request = self.context["request"]
            for pbm in pbms:
                if not isinstance(pbm, RequestableModel | RequestableChildModel):
                    raise ValidationError(f"'{pbm}' is not requestable")
                if not user_can_request(pbm, request.user, request):
                    raise ValidationError(f"Cannot request access to '{pbm.requestable_label}'")
            return pbms

    class GrantRequestFulfillSerializer(PassiveSerializer):

        data = JSONDictField()
        status = ChoiceField(choices=RequestStatus.choices)

    def _assert_reviewer(self, request: Request, grant: GrantRequest):
        rules = RequestRule.objects.filter(targets__in=grant.targets.all()).distinct()
        engine = ListPolicyEngine(rules, request.user, request)
        # A rule with no reviewer bindings at all has nobody configured to approve
        # it -- unlike app access, absence of bindings must not mean "anyone passes".
        engine.empty_result = False
        passing_rules = engine.build().result
        if rules.exclude(pk__in=passing_rules).exists():
            raise ValidationError("User does not have permissions to act on this object")

    def destroy(self, request: Request, *args, **kwargs):
        grant: GrantRequest = self.get_object()
        if grant.status != RequestStatus.CREATED:
            raise ValidationError("Only a pending request can be cancelled")
        return super().destroy(request, *args, **kwargs)

    @extend_schema(responses={200: GrantRequestSerializer(many=True)})
    @action(detail=False, methods=[HTTPMethod.GET])
    def pending_review(self, request: Request) -> Response:
        """List pending grant requests the current user is eligible to review."""
        engine = ListPolicyEngine(RequestRule.objects.all(), request.user, request)
        # A rule with no reviewer bindings at all has nobody configured to approve
        # it -- unlike app access, absence of bindings must not mean "anyone passes".
        engine.empty_result = False
        reviewable_rules = engine.build().result
        queryset = (
            GrantRequest.objects.filter(
                status=RequestStatus.CREATED,
                targets__request_rules__in=reviewable_rules,
            )
            .distinct()
            .order_by("-created")
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(request=GrantRequestCreateSerializer, responses={200: LinkSerializer})
    @validate(GrantRequestCreateSerializer)
    def create(self, request: Request, body: GrantRequestCreateSerializer) -> Response:
        brand: Brand = request.brand
        pbms = body.validated_data["pbms"]
        rule_bindings = list(
            granting_rule_bindings(pbms, request.user, request).select_related("rule")
        )
        # If every rule that granted access to one of the requested pbms agrees on a
        # single request flow, prefer it over the brand's default.
        flow = brand.flow_request
        shared_flows = {rb.rule.request_flow_id for rb in rule_bindings}
        if len(shared_flows) == 1:
            (shared_flow_pk,) = shared_flows
            if shared_flow_pk is not None:
                flow = Flow.objects.get(pk=shared_flow_pk)
        if not flow:
            raise Http404
        planner = FlowPlanner(flow)
        planner.allow_empty_flows = True
        # The strictest (shortest) pending/max expiry among the bindings that actually
        # granted this request wins, so access can never outlive the tightest rule that
        # applies. The requester's override is passed through as-is (not clamped here) --
        # a stage in the flow may still change it, so GrantRequestFinalStageView enforces
        # the maximum once the flow has actually run.
        pending_binding = min(
            rule_bindings, key=lambda rb: timedelta_from_string(rb.expiry_pending)
        )
        max_binding = min(
            rule_bindings, key=lambda rb: timedelta_from_string(rb.expiry_granted_max)
        )
        plan = planner.plan(
            request,
            {
                PLAN_CONTEXT_GRANT_REQUESTED_PBMS: pbms,
                PLAN_CONTEXT_PENDING_USER: request.user,
                PLAN_CONTEXT_GRANT_PENDING_EXPIRY: pending_binding.expiry_pending,
                PLAN_CONTEXT_GRANT_MAX_EXPIRY: max_binding.expiry_granted_max,
                PLAN_CONTEXT_GRANT_REQUESTED_EXPIRY: body.validated_data.get("expiry") or None,
            },
        )
        plan.append_stage(in_memory_stage(GrantRequestFinalStageView))
        return Response({"link": plan.to_redirect(request, flow).url})

    @extend_schema(
        request=GrantRequestFulfillSerializer,
        responses={
            204: OpenApiResponse(description="Request fulfilled"),
        },
    )
    @action([HTTPMethod.PATCH], detail=True, permission_classes=[IsAuthenticated])
    @validate(GrantRequestFulfillSerializer)
    @permission_required("fulfill_grantrequest")
    def fulfill(self, request: Request, body: GrantRequestFulfillSerializer, *args, **kwargs):
        grant: GrantRequest = self.get_object()
        if request.user.pk == grant.created_by_id:
            raise ValidationError("Cannot fulfill your own request")
        self._assert_reviewer(request, grant)
        grant.record_approval(
            request,
            request.user,
            body.validated_data.get("status"),
            data=body.validated_data.get("data"),
        )
        return Response(status=204)

    @extend_schema(
        request=None,
        responses={
            204: OpenApiResponse(description="Grant revoked"),
        },
    )
    @action([HTTPMethod.DELETE], detail=True, permission_classes=[IsAuthenticated])
    @permission_required("revoke_grantrequest")
    def revoke(self, request: Request, *args, **kwargs):
        """Immediately end an active grant. Available to the same reviewers who could
        approve it in the first place."""
        grant: GrantRequest = self.get_object()
        self._assert_reviewer(request, grant)
        grant.revoke(request, request.user)
        return Response(status=204)
