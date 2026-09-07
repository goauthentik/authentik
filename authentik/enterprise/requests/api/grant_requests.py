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


def _owner_holds(
    pbms: list[PolicyBindingModel], owner: User, request: Request
) -> set[PolicyBindingModel]:
    """The subset of `pbms` that `owner` already has access to."""
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
    """A `RequestRuleBinding` expiry field default. RequestRules play no part in an agent's
    request, so it has no binding to take a duration from -- borrowing their defaults keeps
    agent grants in step with the rest of the requests system rather than inventing a knob."""
    return timedelta_from_string(RequestRuleBinding._meta.get_field(field_name).default)


class GrantRequestSerializer(EnterpriseRequiredMixin, ModelSerializer):

    created_by = PartialUserSerializer(read_only=True)
    revoked_by = PartialUserSerializer(read_only=True, allow_null=True)
    agent_owner = PartialUserSerializer(read_only=True, allow_null=True)
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

    class AgentGrantRequestCreatedSerializer(PassiveSerializer):
        """Response to an agent's access request: the request it created, plus the URL to hand to
        the human it acts for. An agent has no browser, so it cannot run the approval itself --
        `fulfill_url` is what its owner opens to approve or deny."""

        grant_request = GrantRequestSerializer(read_only=True)
        fulfill_url = CharField(read_only=True)

    def _assert_reviewer(self, request: Request, grant: GrantRequest):
        # An agent's request is decided by its owner and nobody else -- it only ever delegates
        # access the owner already holds, so rules attached to the target play no part. A rule
        # reviewer must not be able to deny it (a denial finalizes immediately) or revoke it.
        if grant.agent_owner_id:
            if request.user.pk != grant.agent_owner_id:
                raise ValidationError("User does not have permissions to act on this object")
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
                # An agent's request is its owner's to decide alone, so it reaches them through
                # ownership rather than reviewer eligibility -- and must not reach a rule
                # reviewer, who could no longer act on it anyway.
                Q(targets__request_rules__in=reviewable_rules, agent_owner__isnull=True)
                | Q(agent_owner=request.user),
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
        """Delegate access an agent's owner already holds to the agent, time-boxed. Unlike
        `create` this persists the request directly instead of returning a flow link -- an agent
        authenticates with an API token and has no browser to run a flow in, so no justification
        is ever collected. That is why the agent may only ask for what its owner already has:
        the owner's approval is then the whole decision, and no reviewer is asked to judge a
        request with nothing in it. The returned `fulfill_url` is what the agent hands to its
        owner so they can act on it."""
        agent = Agent.objects.filter(pk=request.user.pk).first()
        if not agent:
            raise PermissionDenied(_("Only agents can request access through this endpoint."))
        owner: User | None = agent.parent
        if not owner:
            raise PermissionDenied(_("This agent has no owner who could approve its request."))
        # Delegated access is time-boxed by the agent's own lifetime, so a standing agent has
        # nothing to bound the grant with.
        if not (agent.expiring and agent.expires):
            raise PermissionDenied(_("Only agents with an expiry can request access."))

        pbms = body.validated_data["pbms"]
        # An agent can never reach past its owner: it may only be delegated access the owner
        # already holds. Anything more would need the requester's justification and the reviewer
        # flow that collects it, and this endpoint has no flow to run.
        owner_holds = _owner_holds(pbms, owner, request)
        for pbm in pbms:
            if pbm.pbm_uuid not in owner_holds:
                raise ValidationError(f"Cannot request access to '{pbm.requestable_label}'")

        # No RequestRule gates this request, so there is no binding to take a duration from.
        # The grant is additionally capped so it can never outlive the agent holding it.
        pending_expiry = _binding_default("expiry_pending")
        granted_expiry = min(
            _binding_default("expiry_granted_max"), max(agent.expires - now(), timedelta(0))
        )

        req = create_grant_request(
            request,
            created_by=agent,
            pbms=pbms,
            requester_data={},
            expiry=GrantExpiry(pending=pending_expiry, granted=granted_expiry),
            agent_owner=owner,
        )
        return Response(
            self.AgentGrantRequestCreatedSerializer(
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
