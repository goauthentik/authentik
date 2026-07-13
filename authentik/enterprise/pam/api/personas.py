from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import PermissionDenied
from rest_framework.fields import CharField
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
from authentik.core.models import User
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.pam.models import Persona, PersonaTemplate


class PersonaSerializer(EnterpriseRequiredMixin, PartialUserSerializer):

    parent = PartialUserSerializer(read_only=True)

    class Meta:
        model = Persona
        fields = PartialUserSerializer.Meta.fields + [
            "uuid",
            "expiring",
            "expires",
            "parent",
            "template",
        ]


class PersonaViewSet(
    RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, ListModelMixin, GenericViewSet
):

    queryset = Persona.objects.all()
    serializer_class = PersonaSerializer
    # Users without a global view_persona permission only see/manage their own personas.
    # Updates are additionally gated in perform_update below: owner_field must not let a
    # persona's own parent grant themselves new actor_providers/actor_sources.
    owner_field = "parent"

    class PersonaCreateSerializer(PassiveSerializer):
        name = CharField(required=True)
        as_user = PrimaryKeyRelatedField(queryset=User.objects.all())
        # Determines which actors may delegate to this persona; see PersonaTemplate.
        template = PrimaryKeyRelatedField(
            queryset=PersonaTemplate.objects.all(), required=False, allow_null=True
        )

    @extend_schema(request=PersonaCreateSerializer, responses={201: PersonaSerializer})
    @validate(PersonaCreateSerializer)
    def create(self, request: Request, body: PersonaCreateSerializer) -> Response:
        persona = Persona.create_for_user(
            body.validated_data["name"],
            body.validated_data["as_user"],
            template=body.validated_data.get("template"),
        )
        return Response(PersonaSerializer(instance=persona).data, status=201)

    def perform_update(self, serializer):
        # owner_field grants the persona's own parent object-level access so they can see
        # and revoke (delete) their own persona, but reassigning which template (and so
        # which actors) may delegate to it is a materially bigger privilege that must stay
        # admin-only, so it's required explicitly here rather than relying on owner_field.
        if not self.request.user.has_perm("authentik_pam.change_persona"):
            raise PermissionDenied("Only admins may edit personas.")
        serializer.save()
