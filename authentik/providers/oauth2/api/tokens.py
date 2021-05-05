"""OAuth2Provider API Views"""
from guardian.utils import get_anonymous_user
from rest_framework import mixins
from rest_framework.fields import CharField, ListField
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import GenericViewSet

from authentik.core.api.users import UserSerializer
from authentik.core.api.utils import MetaNameSerializer
from authentik.providers.oauth2.api.provider import OAuth2ProviderSerializer
from authentik.providers.oauth2.models import AuthorizationCode, RefreshToken


class ExpiringBaseGrantModelSerializer(ModelSerializer, MetaNameSerializer):
    """Serializer for BaseGrantModel and ExpiringBaseGrant"""

    user = UserSerializer()
    provider = OAuth2ProviderSerializer()
    scope = ListField(child=CharField())

    class Meta:

        model = AuthorizationCode
        fields = ["pk", "provider", "user", "is_expired", "expires", "scope"]
        depth = 2


class AuthorizationCodeViewSet(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """AuthorizationCode Viewset"""

    queryset = AuthorizationCode.objects.all()
    serializer_class = ExpiringBaseGrantModelSerializer
    filterset_fields = ["user", "provider"]
    ordering = ["provider", "expires"]

    def get_queryset(self):
        user = self.request.user if self.request else get_anonymous_user()
        if user.is_superuser:
            return super().get_queryset()
        return super().get_queryset().filter(user=user.pk)


class RefreshTokenViewSet(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """RefreshToken Viewset"""

    queryset = RefreshToken.objects.all()
    serializer_class = ExpiringBaseGrantModelSerializer
    filterset_fields = ["user", "provider"]
    ordering = ["provider", "expires"]

    def get_queryset(self):
        user = self.request.user if self.request else get_anonymous_user()
        if user.is_superuser:
            return super().get_queryset()
        return super().get_queryset().filter(user=user.pk)
