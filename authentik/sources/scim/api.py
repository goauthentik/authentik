"""SCIMSource API Views"""
from django.urls import reverse_lazy
from rest_framework.fields import SerializerMethodField
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.sources import SourceSerializer
from authentik.core.api.tokens import TokenSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.models import Token, TokenIntents, User, UserTypes
from authentik.sources.scim.models import SCIMSource


class SCIMSourceSerializer(SourceSerializer):
    """SCIMSource Serializer"""

    root_url = SerializerMethodField()
    token_obj = TokenSerializer(source="token", required=False, read_only=True)

    def get_root_url(self, instance: SCIMSource) -> str:
        """Get Root URL"""
        relative_url = reverse_lazy(
            "authentik_sources_scim:v2-root",
            kwargs={"source_slug": instance.slug},
        )
        if "request" not in self.context:
            return relative_url
        return self.context["request"].build_absolute_uri(relative_url)

    def create(self, validated_data):
        instance: SCIMSource = super().create(validated_data)
        identifier = f"ak-source-scim-{instance.pk}"
        user = User.objects.create(
            username=identifier,
            name=f"SCIM Source {instance.name} Service-Account",
            type=UserTypes.SERVICE_ACCOUNT,
        )
        token = Token.objects.create(
            user=user,
            identifier=identifier,
            intent=TokenIntents.INTENT_API,
            expiring=False,
            managed=f"goauthentik.io/sources/scim/{instance.pk}",
        )
        instance.token = token
        instance.save()
        return instance

    class Meta:

        model = SCIMSource
        fields = SourceSerializer.Meta.fields + ["token", "root_url", "token_obj"]


class SCIMSourceViewSet(UsedByMixin, ModelViewSet):
    """SCIMSource Viewset"""

    queryset = SCIMSource.objects.all()
    serializer_class = SCIMSourceSerializer
    lookup_field = "slug"
    filterset_fields = ["name", "slug"]
    search_fields = ["name", "slug", "token__identifier", "token__user__username"]
    ordering = ["name"]
