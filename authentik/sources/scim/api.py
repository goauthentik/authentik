"""SCIMSource API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.sources import SourceSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.models import USER_ATTRIBUTE_SA, Token, TokenIntents, User
from authentik.sources.scim.models import SCIMSource


class SCIMSourceSerializer(SourceSerializer):
    """SCIMSource Serializer"""

    def create(self, validated_data):
        instance: SCIMSource = super().create(validated_data)
        identifier = f"ak-source-scim-{instance.pk}"
        user = User.objects.create(
            username=identifier,
            name=f"SCIM Source {instance.name} Service-Account",
            attributes={USER_ATTRIBUTE_SA: True},
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
        fields = SourceSerializer.Meta.fields + ["token"]


class SCIMSourceViewSet(UsedByMixin, ModelViewSet):
    """SCIMSource Viewset"""

    queryset = SCIMSource.objects.all()
    serializer_class = SCIMSourceSerializer
    lookup_field = "slug"
    filterset_fields = "__all__"
    search_fields = ["name", "slug", "token__identifier", "token__user__username"]
    ordering = ["name"]
