from rest_framework.mixins import (
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
)
from rest_framework.viewsets import GenericViewSet

from authentik.core.api.groups import PartialUserSerializer
from authentik.pam.models import Persona


class PersonaSerializer(PartialUserSerializer):

    parent = PartialUserSerializer(read_only=True)

    class Meta:
        model = Persona
        fields = PartialUserSerializer.Meta.fields + ["uuid", "expiring", "expires", "parent"]


class PersonaViewSet(RetrieveModelMixin, DestroyModelMixin, ListModelMixin, GenericViewSet):

    queryset = Persona.objects.all()
    serializer_class = PersonaSerializer
