from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import PermissionDenied
from rest_framework.fields import BooleanField, CharField, DateTimeField, SerializerMethodField
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
from authentik.core.models import Application, Token, TokenIntents, User, default_token_duration
from authentik.enterprise.agents.apps import AllowAnyAgentCreate
from authentik.enterprise.agents.models import Agent
from authentik.enterprise.api import EnterpriseRequiredMixin


class AgentSerializer(EnterpriseRequiredMixin, PartialUserSerializer):

    parent = PartialUserSerializer(source="owner", read_only=True)
    token_identifier = SerializerMethodField()
    # The least-privilege allow-list: the agent may act on exactly these applications (and
    # never more than its owner can). Writable so the scope can be managed after creation.
    applications = PrimaryKeyRelatedField(
        many=True, queryset=Application.objects.all(), required=False
    )

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
            "token_identifier",
            "applications",
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
    owner_field = "owner"
    rbac_allow_create_without_perm = True

    class AgentCreateSerializer(PassiveSerializer):

        parent = PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, default=None)
        label = CharField(required=False, allow_blank=True)
        expiring = BooleanField(required=False, default=False)
        expires = DateTimeField(required=False, allow_null=True, default=None)
        applications = PrimaryKeyRelatedField(
            many=True, queryset=Application.objects.all(), required=False, default=list
        )

    @extend_schema(request=AgentCreateSerializer, responses={201: AgentCreatedSerializer})
    @validate(AgentCreateSerializer)
    def create(self, request: Request, body: AgentCreateSerializer) -> Response:
        parent: User = body.validated_data.get("parent") or request.user
        is_admin = request.user.has_perm("authentik_agents.add_agent")
        # Self-service = creating an agent for yourself; provisioning for another user is an
        # admin action. The distinction is ownership, not merely holding the permission.
        self_service = parent == request.user

        if not self_service and not is_admin:
            raise PermissionDenied(_("You can only create agents for yourself."))
        if self_service and not is_admin and not AllowAnyAgentCreate.get():
            raise PermissionDenied(_("Self-service agent creation is not enabled."))

        if self_service:
            # Self-service agents always expire with the tenant default; the caller cannot
            # opt out (even a superuser creating an agent for themselves).
            expiring = True
            expires = default_token_duration()
        else:
            # Provisioning for another user may set a custom/standing expiry.
            expiring = body.validated_data["expiring"]
            expires = body.validated_data["expires"]
        agent = Agent.create_for_user(
            user=parent,
            name=body.validated_data.get("label", ""),
            expiring=expiring,
            expires=expires,
        )
        # Scope the agent to its allow-listed applications (empty = no access).
        agent.applications.set(body.validated_data.get("applications", []))
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
