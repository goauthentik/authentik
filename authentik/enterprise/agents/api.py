from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import PermissionDenied
from rest_framework.fields import (
    BooleanField,
    CharField,
    ChoiceField,
    DateTimeField,
    SerializerMethodField,
)
from rest_framework.mixins import (
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from authentik.api.validation import validate
from authentik.core.api.groups import PartialUserSerializer
from authentik.core.api.utils import PassiveSerializer
from authentik.core.models import (
    ActorPolicyInheritance,
    Token,
    TokenIntents,
    User,
    UserTypes,
    default_token_duration,
)
from authentik.enterprise.agents.models import Agent
from authentik.enterprise.api import EnterpriseRequiredMixin, enterprise_action


class AgentSerializer(EnterpriseRequiredMixin, PartialUserSerializer):

    parent = PartialUserSerializer(read_only=True)
    # Chosen at creation only; immutable afterwards.
    policy_behavior = ChoiceField(choices=ActorPolicyInheritance.choices, read_only=True)
    token_identifier = SerializerMethodField()

    def get_token_identifier(self, agent: Agent) -> str | None:
        """Identifier of the agent's API token, so its key can be retrieved/copied later."""
        token = Token.objects.filter(user=agent, intent=TokenIntents.INTENT_API).first()
        return token.identifier if token else None

    class Meta:
        model = Agent
        fields = PartialUserSerializer.Meta.fields + [
            "uuid",
            "expiring",
            "expires",
            "parent",
            "policy_behavior",
            "token_identifier",
        ]


class AgentCreatedSerializer(PassiveSerializer):
    """Response returned once when an agent is created, carrying the one-time API token."""

    agent = AgentSerializer(read_only=True)
    token = CharField(read_only=True)


class AgentViewSet(
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    GenericViewSet,
):
    """Admin-provisioned delegate identities. An admin creates a Agent for a given
    parent user, then grants it access the same way as any other User -- ordinary
    PolicyBindings pointed at whatever it needs."""

    queryset = Agent.objects.all()
    serializer_class = AgentSerializer
    owner_field = "parent"
    rbac_allow_create_without_perm = True
    filterset_fields = ["parent"]

    class AgentCreateSerializer(PassiveSerializer):

        parent = PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, default=None)
        label = CharField(required=False, allow_blank=True)
        expiring = BooleanField(required=False, default=False)
        expires = DateTimeField(required=False, allow_null=True, default=None)
        policy_behavior = ChoiceField(
            choices=ActorPolicyInheritance.choices,
            default=ActorPolicyInheritance.MIRROR,
            required=False,
        )

    @extend_schema(request=AgentCreateSerializer, responses={201: AgentCreatedSerializer})
    @validate(AgentCreateSerializer)
    @enterprise_action
    def create(self, request: Request, body: AgentCreateSerializer) -> Response:
        parent: User = body.validated_data.get("parent") or request.user
        self_service_perm = request.user.has_perm("authentik_agents.add_agent_self_service")
        admin_perm = request.user.has_perm("authentik_agents.add_agent")
        # Self-service = creating an agent for yourself; provisioning for another user is an
        # admin action. The distinction is ownership, not merely holding the permission.
        self_service = parent == request.user

        if not admin_perm:
            if not self_service:
                raise PermissionDenied(_("You can only create agents for yourself."))
            if not self_service_perm:
                raise PermissionDenied(_("Self-service agent creation is not enabled."))
            if request.user.type != UserTypes.INTERNAL:
                raise PermissionDenied(_("Only internal user accounts can create agents."))

        if self_service:
            # Self-service agents are least-privilege by construction: they always expire with the
            # tenant default and inherit NO access from their owner. They earn access the same way
            # a human does -- by filing a grant request their owner approves (see
            # authentik.enterprise.requests).
            expiring = True
            expires = default_token_duration()
            policy_behavior = ActorPolicyInheritance.NONE
        else:
            # Provisioning for another user may set a custom/standing expiry and policy behavior.
            expiring = body.validated_data["expiring"]
            expires = body.validated_data["expires"]
            policy_behavior = body.validated_data["policy_behavior"]
        agent = Agent.create_for_user(
            user=parent,
            name=body.validated_data.get("label", ""),
            expiring=expiring,
            expires=expires,
            policy_behavior=policy_behavior,
        )
        # Issue an API token so a harness can authenticate as the agent (Bearer auth).
        token = Token.objects.create(
            identifier=agent.username,
            intent=TokenIntents.INTENT_API,
            user=agent,
            expiring=True,
            expires=default_token_duration(),
        )
        parent.assign_perms_to_managed_role(
            [
                "authentik_agents.view_agent",
                "authentik_agents.change_agent",
                "authentik_agents.delete_agent",
            ],
            agent,
        )
        # Grant the owner access to the token key so it stays retrievable after creation.
        parent.assign_perms_to_managed_role("authentik_core.view_token_key", token)
        return Response(
            AgentCreatedSerializer({"agent": agent, "token": token.key}).data, status=201
        )
