"""User API Views"""
from django.db.models.base import Model
from django.urls import reverse_lazy
from django.utils.http import urlencode
from drf_yasg2.utils import swagger_auto_schema, swagger_serializer_method
from guardian.utils import get_anonymous_user
from rest_framework.decorators import action
from rest_framework.fields import CharField, SerializerMethodField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BooleanField, ModelSerializer, Serializer
from rest_framework.viewsets import ModelViewSet

from authentik.admin.api.metrics import CoordinateSerializer, get_events_per_1h
from authentik.api.decorators import permission_required
from authentik.core.middleware import (
    SESSION_IMPERSONATE_ORIGINAL_USER,
    SESSION_IMPERSONATE_USER,
)
from authentik.core.models import Token, TokenIntents, User
from authentik.events.models import EventAction


class UserSerializer(ModelSerializer):
    """User Serializer"""

    is_superuser = BooleanField(read_only=True)
    avatar = CharField(read_only=True)

    class Meta:

        model = User
        fields = [
            "pk",
            "username",
            "name",
            "is_active",
            "last_login",
            "is_superuser",
            "email",
            "avatar",
            "attributes",
        ]


class SessionUserSerializer(Serializer):
    """Response for the /user/me endpoint, returns the currently active user (as `user` property)
    and, if this user is being impersonated, the original user in the `original` property."""

    user = UserSerializer()
    original = UserSerializer(required=False)

    def create(self, validated_data: dict) -> Model:
        raise NotImplementedError

    def update(self, instance: Model, validated_data: dict) -> Model:
        raise NotImplementedError


class UserRecoverySerializer(Serializer):
    """Recovery link for a user to reset their password"""

    link = CharField()

    def create(self, validated_data: dict) -> Model:
        raise NotImplementedError

    def update(self, instance: Model, validated_data: dict) -> Model:
        raise NotImplementedError


class UserMetricsSerializer(Serializer):
    """User Metrics"""

    logins_per_1h = SerializerMethodField()
    logins_failed_per_1h = SerializerMethodField()
    authorizations_per_1h = SerializerMethodField()

    @swagger_serializer_method(serializer_or_field=CoordinateSerializer(many=True))
    def get_logins_per_1h(self, _):
        """Get successful logins per hour for the last 24 hours"""
        request = self.context["request"]._request
        return get_events_per_1h(action=EventAction.LOGIN, user__pk=request.user.pk)

    @swagger_serializer_method(serializer_or_field=CoordinateSerializer(many=True))
    def get_logins_failed_per_1h(self, _):
        """Get failed logins per hour for the last 24 hours"""
        request = self.context["request"]._request
        return get_events_per_1h(
            action=EventAction.LOGIN_FAILED, context__username=request.user.username
        )

    @swagger_serializer_method(serializer_or_field=CoordinateSerializer(many=True))
    def get_authorizations_per_1h(self, _):
        """Get failed logins per hour for the last 24 hours"""
        request = self.context["request"]._request
        return get_events_per_1h(
            action=EventAction.AUTHORIZE_APPLICATION, user__pk=request.user.pk
        )

    def create(self, validated_data: dict) -> Model:
        raise NotImplementedError

    def update(self, instance: Model, validated_data: dict) -> Model:
        raise NotImplementedError


class UserViewSet(ModelViewSet):
    """User Viewset"""

    queryset = User.objects.none()
    serializer_class = UserSerializer
    search_fields = ["username", "name", "is_active"]
    filterset_fields = ["username", "name", "is_active"]

    def get_queryset(self):
        return User.objects.all().exclude(pk=get_anonymous_user().pk)

    @swagger_auto_schema(responses={200: SessionUserSerializer(many=False)})
    @action(detail=False)
    # pylint: disable=invalid-name
    def me(self, request: Request) -> Response:
        """Get information about current user"""
        serializer = SessionUserSerializer(
            data={"user": UserSerializer(request.user).data}
        )
        if SESSION_IMPERSONATE_USER in request._request.session:
            serializer.initial_data["original"] = UserSerializer(
                request._request.session[SESSION_IMPERSONATE_ORIGINAL_USER]
            ).data
        serializer.is_valid()
        return Response(serializer.data)

    @permission_required("authentik_core.view_user", ["authentik_events.view_event"])
    @swagger_auto_schema(responses={200: UserMetricsSerializer(many=False)})
    @action(detail=False)
    def metrics(self, request: Request) -> Response:
        """User metrics per 1h"""
        serializer = UserMetricsSerializer(True)
        serializer.context["request"] = request
        return Response(serializer.data)

    @permission_required("authentik_core.reset_user_password")
    @swagger_auto_schema(
        responses={"200": UserRecoverySerializer(many=False)},
    )
    @action(detail=True)
    # pylint: disable=invalid-name, unused-argument
    def recovery(self, request: Request, pk: int) -> Response:
        """Create a temporary link that a user can use to recover their accounts"""
        user: User = self.get_object()
        token, __ = Token.objects.get_or_create(
            identifier=f"{user.uid}-password-reset",
            user=user,
            intent=TokenIntents.INTENT_RECOVERY,
        )
        querystring = urlencode({"token": token.key})
        link = request.build_absolute_uri(
            reverse_lazy("authentik_flows:default-recovery") + f"?{querystring}"
        )
        return Response({"link": link})
