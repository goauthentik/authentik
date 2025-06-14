"""OAuth2Provider API Views"""

from json import dumps

from django_filters.rest_framework import DjangoFilterBackend
from guardian.utils import get_anonymous_user
from rest_framework import mixins
from rest_framework.fields import CharField, ListField, SerializerMethodField
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import GenericViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.users import UserSerializer
from authentik.core.api.utils import MetaNameSerializer, ModelSerializer
from authentik.providers.oauth2.api.providers import OAuth2ProviderSerializer
from authentik.providers.oauth2.models import AccessToken, AuthorizationCode, RefreshToken


class ExpiringBaseGrantModelSerializer(ModelSerializer, MetaNameSerializer):
    """Serializer for BaseGrantModel and ExpiringBaseGrant"""

    user = UserSerializer()
    provider = OAuth2ProviderSerializer()
    scope = ListField(child=CharField())

    class Meta:
        model = AuthorizationCode
        fields = ["pk", "provider", "user", "is_expired", "expires", "scope"]
        depth = 2


class TokenModelSerializer(ExpiringBaseGrantModelSerializer):
    """Serializer for BaseGrantModel and RefreshToken"""

    id_token = SerializerMethodField()

    def get_id_token(self, instance: RefreshToken) -> str:
        """Get the token's id_token as JSON String"""
        return dumps(instance.id_token.to_dict(), indent=4)

    class Meta:
        model = RefreshToken
        fields = [
            "pk",
            "provider",
            "user",
            "is_expired",
            "expires",
            "scope",
            "id_token",
            "revoked",
        ]
        depth = 2


class AuthorizationCodeViewSet(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """AuthorizationCode Viewset"""

    queryset = AuthorizationCode.objects.all()
    serializer_class = ExpiringBaseGrantModelSerializer
    filterset_fields = ["user", "provider"]
    ordering = ["provider", "expires"]
    filter_backends = [
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]

    def get_queryset(self):
        user = self.request.user if self.request else get_anonymous_user()
        if user.is_superuser:
            return super().get_queryset()
        return super().get_queryset().filter(user=user.pk)


class RefreshTokenViewSet(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """RefreshToken Viewset"""

    queryset = RefreshToken.objects.all()
    serializer_class = TokenModelSerializer
    filterset_fields = ["user", "provider"]
    ordering = ["provider", "expires"]
    filter_backends = [
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]

    def get_queryset(self):
        user = self.request.user if self.request else get_anonymous_user()
        if user.is_superuser:
            return super().get_queryset()
        return super().get_queryset().filter(user=user.pk)


class AccessTokenViewSet(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """AccessToken Viewset"""

    queryset = AccessToken.objects.all()
    serializer_class = TokenModelSerializer
    filterset_fields = ["user", "provider"]
    ordering = ["provider", "expires"]
    filter_backends = [
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]

    def get_queryset(self):
        user = self.request.user if self.request else get_anonymous_user()
        if user.is_superuser:
            return super().get_queryset()
        return super().get_queryset().filter(user=user.pk)
