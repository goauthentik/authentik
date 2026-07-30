from drf_spectacular.utils import extend_schema
from rest_framework.fields import BooleanField, CharField, DateTimeField
from rest_framework.mixins import DestroyModelMixin, ListModelMixin, RetrieveModelMixin
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from authentik.api.validation import validate
from authentik.core.api.groups import PartialUserSerializer
from authentik.core.api.utils import PassiveSerializer
from authentik.core.models import User
from authentik.enterprise.agents.models import Agent
from authentik.enterprise.api import EnterpriseRequiredMixin


class AgentSerializer(EnterpriseRequiredMixin, PartialUserSerializer):

    parent = PartialUserSerializer(read_only=True)

    class Meta:
        model = Agent
        fields = PartialUserSerializer.Meta.fields + ["uuid", "expiring", "expires", "parent"]


class AgentViewSet(RetrieveModelMixin, DestroyModelMixin, ListModelMixin, GenericViewSet):
    """Admin-provisioned delegate identities. An admin creates a Agent for a given
    parent user, then grants it access the same way as any other User -- ordinary
    PolicyBindings pointed at whatever it needs."""

    queryset = Agent.objects.all()
    serializer_class = AgentSerializer

    class AgentCreateSerializer(PassiveSerializer):

        parent = PrimaryKeyRelatedField(queryset=User.objects.all())
        label = CharField(required=False, allow_blank=True)
        expiring = BooleanField(required=False, default=False)
        expires = DateTimeField(required=False, allow_null=True, default=None)

    @extend_schema(request=AgentCreateSerializer, responses={201: AgentSerializer})
    @validate(AgentCreateSerializer)
    def create(self, request: Request, body: AgentCreateSerializer) -> Response:
        parent: User = body.validated_data["parent"]
        agent = Agent.objects.create(
            owner=parent,
            primary_app=None,
        )
        parent.assign_perms_to_managed_role(
            ["authentik_requests.view_agent", "authentik_requests.delete_agent"],
            agent,
        )
        return Response(AgentSerializer(instance=agent).data, status=201)
