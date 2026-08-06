from datetime import timedelta
from http import HTTPMethod

from django.db.models import Q
from django.http import Http404
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_field
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
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
from authentik.core.apps import AppAccessWithoutBindings
from authentik.core.models import User
from authentik.enterprise.agents.models import Agent
from authentik.enterprise.api import EnterpriseRequiredMixin, enterprise_action
from authentik.enterprise.requests.api.apps import (
    RequestableTargetSerializer,
    granting_rule_bindings,
    user_can_request,
)
from authentik.enterprise.requests.grants import (
    GrantExpiry,
    create_grant_request,
    fulfill_url,
)
from authentik.enterprise.requests.models import (
    GrantRequest,
    RequestRule,
    RequestRuleBinding,
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


def _owner_holds(pbms: list[PolicyBindingModel], owner: User, request: Request) -> set:
    """The subset of `pbms` that `owner` already has access to.

    An application and one of its child objects disagree on what "no bindings" means: an
    application with none is reachable by anyone (`AppAccessWithoutBindings`), while an
    entitlement with none is held by nobody -- `User.app_entitlements` only ever counts an
    enabled, matching binding. So each kind is evaluated with its own `empty_result` rather
    than under one blanket rule. Still batched: one engine pass per kind, not per target.
    """
    children = [pbm for pbm in pbms if isinstance(pbm, RequestableChildModel)]
    parents = [pbm for pbm in pbms if not isinstance(pbm, RequestableChildModel)]
    held = set()
    for targets, empty_result in ((parents, AppAccessWithoutBindings.get()), (children, False)):
        if not targets:
            continue
        engine = ListPolicyEngine(
            PolicyBindingModel.objects.filter(pbm_uuid__in=[pbm.pbm_uuid for pbm in targets]),
            owner,
            request,
        )
        engine.empty_result = empty_result
        held |= {obj.pbm_uuid for obj in engine.build().result}
    return held


def _binding_default(field_name: str) -> timedelta:
    """A `RequestRuleBinding` expiry default, used when a request carries no granting binding
    at all (an agent requesting a target its owner already has access to)."""
    return timedelta_from_string(RequestRuleBinding._meta.get_field(field_name).default)


class GrantRequestSerializer(EnterpriseRequiredMixin, ModelSerializer):

    created_by = PartialUserSerializer(read_only=True)
    revoked_by = PartialUserSerializer(read_only=True)
    agent_owner = PartialUserSerializer(read_only=True)
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
            "agent_owner",
            "rules_approval_required",
            "is_active",
            "expires",
            "status",
            "targets",
            "target_objs",
            "uuid",
        ]
        extra_kwargs = {
            "status": {"read_only": True},
            "rules_approval_required": {"read_only": True},
        }


class AgentGrantRequestCreatedSerializer(PassiveSerializer):
    """Response to an agent's access request: the request it created, plus the URL to hand to
    the human it acts for. An agent has no browser, so it cannot run the approval itself --
    `fulfill_url` is what its owner opens to approve or deny."""

    grant_request = GrantRequestSerializer(read_only=True)
    fulfill_url = CharField(read_only=True)


class GrantRequestViewSet(RetrieveModelMixin, DestroyModelMixin, ListModelMixin, GenericViewSet):

    # All requests are visible to users even if they're expired
    queryset = GrantRequest.objects.including_expired()
    serializer_class = GrantRequestSerializer
    filterset_fields = ["created_by", "agent_owner", "status"]
    rbac_allow_create_without_perm = True

    class GrantRequestCreateSerializer(PassiveSerializer):

        pbms = PolicyBindingModelForeignKey(
            queryset=PolicyBindingModel.objects.select_subclasses(),
            many=True,
            allow_empty=False,
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
            # De-dupe by pk so a caller passing the same target twice can't mint duplicate
            # GrantRequestTargets (and therefore duplicate granted PolicyBindings).
            deduped = list({pbm.pk: pbm for pbm in pbms}.values())
            for pbm in deduped:
                if not isinstance(pbm, RequestableModel | RequestableChildModel):
                    raise ValidationError(f"'{pbm}' is not requestable")
                if not user_can_request(pbm, request.user, request):
                    raise ValidationError(f"Cannot request access to '{pbm.requestable_label}'")
            return deduped

    class AgentGrantRequestCreateSerializer(PassiveSerializer):
        """Body for an agent requesting access for itself. Deliberately narrower than
        `GrantRequestCreateSerializer`: an agent may not pick its own expiry, which is
        derived from the granting rules and capped by the agent's own lifetime."""

        pbms = PolicyBindingModelForeignKey(
            queryset=PolicyBindingModel.objects.select_subclasses(),
            many=True,
            allow_empty=False,
        )

        def validate_pbms(self, pbms: list[PolicyBindingModel]) -> list[PolicyBindingModel]:
            deduped = list({pbm.pk: pbm for pbm in pbms}.values())
            for pbm in deduped:
                if not isinstance(pbm, RequestableModel | RequestableChildModel):
                    raise ValidationError(f"'{pbm}' is not requestable")
            return deduped

    class GrantRequestFulfillSerializer(PassiveSerializer):

        data = JSONDictField()
        status = ChoiceField(choices=RequestStatus.choices)

    def _assert_reviewer(self, request: Request, grant: GrantRequest):
        # An agent's owner is always entitled to act on their own agent's request, whether or
        # not any rule attached to its targets makes them an eligible reviewer -- and a request
        # for a target the owner already has access to may carry no rule at all.
        if grant.agent_owner_id and request.user.pk == grant.agent_owner_id:
            return
        rules = RequestRule.objects.filter(targets__in=grant.targets.all()).distinct()
        engine = ListPolicyEngine(rules, request.user, request)
        # A rule with no reviewer bindings at all has nobody configured to approve
        # it -- unlike app access, absence of bindings must not mean "anyone passes".
        engine.empty_result = False
        passing_rules = engine.build().result
        # The user only needs to be an eligible reviewer of *at least one* rule attached
        # to the request's targets -- rules are satisfied independently (see
        # GrantRequest.is_satisfied), and this must match what `pending_review` lists.
        if rules.exists() and not passing_rules.exists():
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
                # An agent's owner must approve its request even when its targets carry no rule
                # they could ever review, so surface those alongside the reviewable ones.
                Q(targets__request_rules__in=reviewable_rules) | Q(agent_owner=request.user),
                status=RequestStatus.CREATED,
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
        request=AgentGrantRequestCreateSerializer,
        responses={201: AgentGrantRequestCreatedSerializer},
    )
    @action([HTTPMethod.POST], detail=False, permission_classes=[IsAuthenticated])
    @validate(AgentGrantRequestCreateSerializer)
    @enterprise_action
    def agent(self, request: Request, body: AgentGrantRequestCreateSerializer) -> Response:
        """Request access as an agent, for itself. Unlike `create`, this persists the request
        directly instead of returning a flow link -- an agent authenticates with an API token
        and has no browser to run a flow in. Eligibility is always evaluated against the
        agent's owner, whose approval is mandatory; the returned `fulfill_url` is what the
        agent surfaces to that owner so they can act on it."""
        agent = Agent.objects.filter(pk=request.user.pk).first()
        if not agent:
            raise PermissionDenied(_("Only agents can request access through this endpoint."))
        owner: User | None = agent.parent
        if not owner:
            raise PermissionDenied(_("This agent has no owner who could approve its request."))

        pbms = body.validated_data["pbms"]
        # An agent can never reach past its owner, so every target is judged against the owner
        # -- under NONE inheritance the agent itself passes nothing of its own.
        owner_holds = _owner_holds(pbms, owner, request)
        # A target the owner already holds leaves nothing for the regular reviewer flow to
        # decide -- their own approval suffices. Anything else must at least be requestable by
        # them, and drags the request through the rules. Strictest wins across a mixed batch.
        rules_approval_required = False
        for pbm in pbms:
            if pbm.pbm_uuid in owner_holds:
                continue
            if not user_can_request(pbm, owner, request):
                raise ValidationError(f"Cannot request access to '{pbm.requestable_label}'")
            rules_approval_required = True

        # The strictest (shortest) pending/max expiry among the bindings that make this
        # requestable wins, as in `create`. With no granting binding at all -- the owner already
        # had access -- fall back to the binding defaults.
        rule_bindings = list(granting_rule_bindings(pbms, owner, request))
        pending_expiry = _binding_default("expiry_pending")
        granted_expiry = _binding_default("expiry_granted_max")
        if rule_bindings:
            pending_expiry = min(timedelta_from_string(rb.expiry_pending) for rb in rule_bindings)
            granted_expiry = min(
                timedelta_from_string(rb.expiry_granted_max) for rb in rule_bindings
            )
        # A grant must never outlive the agent holding it. Self-service agents always expire,
        # so this ceiling always applies to them.
        if agent.expiring and agent.expires:
            granted_expiry = min(granted_expiry, max(agent.expires - now(), timedelta(0)))

        req = create_grant_request(
            request,
            created_by=agent,
            pbms=pbms,
            requester_data={},
            expiry=GrantExpiry(pending=pending_expiry, granted=granted_expiry),
            agent_owner=owner,
            rules_approval_required=rules_approval_required,
        )
        return Response(
            AgentGrantRequestCreatedSerializer(
                {"grant_request": req, "fulfill_url": fulfill_url(request, req)}
            ).data,
            status=201,
        )

    @extend_schema(
        request=GrantRequestFulfillSerializer,
        responses={
            204: OpenApiResponse(description="Request fulfilled"),
        },
    )
    @action([HTTPMethod.PATCH], detail=True, permission_classes=[IsAuthenticated])
    @validate(GrantRequestFulfillSerializer)
    @permission_required("authentik_requests.fulfill_grantrequest")
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
    @permission_required("authentik_requests.revoke_grantrequest")
    def revoke(self, request: Request, *args, **kwargs):
        """Immediately end an active grant. Available to the same reviewers who could
        approve it in the first place."""
        grant: GrantRequest = self.get_object()
        self._assert_reviewer(request, grant)
        grant.revoke(request, request.user)
        return Response(status=204)
