"""User API Views"""
from authentik.core.api.groups import GroupSerializer
from django.http.response import Http404
from django.urls import reverse_lazy
from django.utils.http import urlencode
from drf_yasg.utils import swagger_auto_schema, swagger_serializer_method
from guardian.utils import get_anonymous_user
from rest_framework.decorators import action
from rest_framework.fields import CharField, JSONField, SerializerMethodField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BooleanField, ListSerializer, ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.admin.api.metrics import CoordinateSerializer, get_events_per_1h
from authentik.api.decorators import permission_required
from authentik.core.api.utils import LinkSerializer, PassiveSerializer, is_dict
from authentik.core.middleware import (
    SESSION_IMPERSONATE_ORIGINAL_USER,
    SESSION_IMPERSONATE_USER,
)
from authentik.core.models import Token, TokenIntents, User
from authentik.events.models import EventAction
from authentik.flows.models import Flow, FlowDesignation


class UserSerializer(ModelSerializer):
    """User Serializer"""

    is_superuser = BooleanField(read_only=True)
    avatar = CharField(read_only=True)
    attributes = JSONField(validators=[is_dict], required=False)
    groups = ListSerializer(child=GroupSerializer(), read_only=True, source="ak_groups")

    class Meta:

        model = User
        fields = [
            "pk",
            "username",
            "name",
            "is_active",
            "last_login",
            "is_superuser",
            "groups",
            "email",
            "avatar",
            "attributes",
        ]


class SessionUserSerializer(PassiveSerializer):
    """Response for the /user/me endpoint, returns the currently active user (as `user` property)
    and, if this user is being impersonated, the original user in the `original` property."""

    user = UserSerializer()
    original = UserSerializer(required=False)


class UserMetricsSerializer(PassiveSerializer):
    """User Metrics"""

    logins_per_1h = SerializerMethodField()
    logins_failed_per_1h = SerializerMethodField()
    authorizations_per_1h = SerializerMethodField()

    @swagger_serializer_method(serializer_or_field=CoordinateSerializer(many=True))
    def get_logins_per_1h(self, _):
        """Get successful logins per hour for the last 24 hours"""
        user = self.context["user"]
        return get_events_per_1h(action=EventAction.LOGIN, user__pk=user.pk)

    @swagger_serializer_method(serializer_or_field=CoordinateSerializer(many=True))
    def get_logins_failed_per_1h(self, _):
        """Get failed logins per hour for the last 24 hours"""
        user = self.context["user"]
        return get_events_per_1h(
            action=EventAction.LOGIN_FAILED, context__username=user.username
        )

    @swagger_serializer_method(serializer_or_field=CoordinateSerializer(many=True))
    def get_authorizations_per_1h(self, _):
        """Get failed logins per hour for the last 24 hours"""
        user = self.context["user"]
        return get_events_per_1h(
            action=EventAction.AUTHORIZE_APPLICATION, user__pk=user.pk
        )


class UserViewSet(ModelViewSet):
    """User Viewset"""

    queryset = User.objects.none()
    serializer_class = UserSerializer
    search_fields = ["username", "name", "is_active"]
    filterset_fields = ["username", "name", "is_active"]

    def get_queryset(self):
        return User.objects.all().exclude(pk=get_anonymous_user().pk)

    @swagger_auto_schema(responses={200: SessionUserSerializer(many=False)})
    @action(detail=False, pagination_class=None, filter_backends=[])
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
    @action(detail=True, pagination_class=None, filter_backends=[])
    # pylint: disable=invalid-name, unused-argument
    def metrics(self, request: Request, pk: int) -> Response:
        """User metrics per 1h"""
        user: User = self.get_object()
        serializer = UserMetricsSerializer(True)
        serializer.context["user"] = user
        return Response(serializer.data)

    @permission_required("authentik_core.reset_user_password")
    @swagger_auto_schema(
        responses={"200": LinkSerializer(many=False), "404": "No recovery flow found."},
    )
    @action(detail=True, pagination_class=None, filter_backends=[])
    # pylint: disable=invalid-name, unused-argument
    def recovery(self, request: Request, pk: int) -> Response:
        """Create a temporary link that a user can use to recover their accounts"""
        # Check that there is a recovery flow, if not return an error
        flow = Flow.with_policy(request, designation=FlowDesignation.RECOVERY)
        if not flow:
            raise Http404
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
