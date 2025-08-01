"""SAML Session API Views"""
from rest_framework.fields import CharField
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.providers.saml.models import SAMLSession
from authentik.rbac.decorators import permission_required


class SAMLSessionSerializer(ModelSerializer):
    """SAMLSession Serializer"""

    provider_name = CharField(source="provider.name", read_only=True)
    username = CharField(source="user.username", read_only=True)

    class Meta:
        model = SAMLSession
        fields = [
            "pk",
            "provider",
            "provider_name",
            "user",
            "username",
            "session",
            "session_index",
            "name_id",
            "name_id_format",
            "created",
            "session_not_on_or_after",
        ]
        read_only_fields = fields


class SAMLSessionViewSet(UsedByMixin, ModelViewSet):
    """SAMLSession Viewset"""

    queryset = SAMLSession.objects.all()
    serializer_class = SAMLSessionSerializer
    search_fields = ["user__username", "session_index", "name_id"]
    ordering = ["-created"]
    filterset_fields = ["provider", "user", "session_index", "name_id"]

    @permission_required("authentik_providers_saml.view_samlsession")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @permission_required("authentik_providers_saml.view_samlsession")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)