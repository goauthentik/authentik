from drf_spectacular.utils import extend_schema
from rest_framework.mixins import (
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
)
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.request import Request
from rest_framework.fields import CharField
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from authentik.api.validation import validate
from authentik.core.api.groups import PartialUserSerializer
from authentik.core.api.utils import PassiveSerializer
from authentik.core.models import User
from authentik.pam.models import Persona


class PersonaSerializer(PartialUserSerializer):

    parent = PartialUserSerializer(read_only=True)

    class Meta:
        model = Persona
        fields = PartialUserSerializer.Meta.fields + ["uuid", "expiring", "expires", "parent"]


class PersonaViewSet(RetrieveModelMixin, DestroyModelMixin, ListModelMixin, GenericViewSet):

    queryset = Persona.objects.all()
    serializer_class = PersonaSerializer

    class PersonaCreateSerializer(PassiveSerializer):
        name = CharField(required=True)
        as_user = PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)

    @extend_schema(request=PersonaCreateSerializer, responses={201: PersonaSerializer})
    @validate(PersonaCreateSerializer)
    def create(self, request: Request, body: PersonaCreateSerializer) -> Response:
        if not request.user.is_superuser:
            body.validated_data["as_user"] = request.user
        persona = Persona.create_for_user(body.validated_data["name"], body.validated_data["as_user"])
        return Response(PersonaSerializer(instance=persona).data, status=201)
