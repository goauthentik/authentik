"""User API Views"""
from django.db.models.base import Model
from drf_yasg2.utils import swagger_auto_schema, swagger_serializer_method
from guardian.utils import get_anonymous_user
from rest_framework.decorators import action
from rest_framework.fields import CharField, SerializerMethodField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BooleanField, ModelSerializer, Serializer
from rest_framework.viewsets import ModelViewSet

from authentik.admin.api.metrics import CoordinateSerializer, get_events_per_1h
from authentik.core.models import User
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

    @swagger_auto_schema(responses={200: UserSerializer(many=False)})
    @action(detail=False)
    # pylint: disable=invalid-name
    def me(self, request: Request) -> Response:
        """Get information about current user"""
        return Response(UserSerializer(request.user).data)

    @swagger_auto_schema(responses={200: UserMetricsSerializer(many=False)})
    @action(detail=False)
    def metrics(self, request: Request) -> Response:
        """User metrics per 1h"""
        serializer = UserMetricsSerializer(True)
        serializer.context["request"] = request
        return Response(serializer.data)
