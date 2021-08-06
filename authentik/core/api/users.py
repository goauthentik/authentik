"""User API Views"""
from json import loads

from django.db.models.query import QuerySet
from django.urls import reverse_lazy
from django.utils.http import urlencode
from django_filters.filters import BooleanFilter, CharFilter
from django_filters.filterset import FilterSet
from drf_spectacular.utils import extend_schema, extend_schema_field
from guardian.utils import get_anonymous_user
from rest_framework.decorators import action
from rest_framework.fields import CharField, JSONField, SerializerMethodField
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import (
    BooleanField,
    ListSerializer,
    ModelSerializer,
    ValidationError,
)
from rest_framework.viewsets import ModelViewSet
from rest_framework_guardian.filters import ObjectPermissionsFilter

from authentik.admin.api.metrics import CoordinateSerializer, get_events_per_1h
from authentik.api.decorators import permission_required
from authentik.core.api.groups import GroupSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import LinkSerializer, PassiveSerializer, is_dict
from authentik.core.middleware import SESSION_IMPERSONATE_ORIGINAL_USER, SESSION_IMPERSONATE_USER
from authentik.core.models import Token, TokenIntents, User
from authentik.events.models import EventAction
from authentik.tenants.models import Tenant


class UserSerializer(ModelSerializer):
    """User Serializer"""

    is_superuser = BooleanField(read_only=True)
    avatar = CharField(read_only=True)
    attributes = JSONField(validators=[is_dict], required=False)
    groups = ListSerializer(child=GroupSerializer(), read_only=True, source="ak_groups")
    uid = CharField(read_only=True)

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
            "uid",
        ]


class UserSelfSerializer(ModelSerializer):
    """User Serializer for information a user can retrieve about themselves and
    update about themselves"""

    is_superuser = BooleanField(read_only=True)
    avatar = CharField(read_only=True)
    groups = ListSerializer(child=GroupSerializer(), read_only=True, source="ak_groups")
    uid = CharField(read_only=True)

    class Meta:

        model = User
        fields = [
            "pk",
            "username",
            "name",
            "is_active",
            "is_superuser",
            "groups",
            "email",
            "avatar",
            "uid",
        ]
        extra_kwargs = {
            "is_active": {"read_only": True},
        }


class SessionUserSerializer(PassiveSerializer):
    """Response for the /user/me endpoint, returns the currently active user (as `user` property)
    and, if this user is being impersonated, the original user in the `original` property."""

    user = UserSelfSerializer()
    original = UserSelfSerializer(required=False)


class UserMetricsSerializer(PassiveSerializer):
    """User Metrics"""

    logins_per_1h = SerializerMethodField()
    logins_failed_per_1h = SerializerMethodField()
    authorizations_per_1h = SerializerMethodField()

    @extend_schema_field(CoordinateSerializer(many=True))
    def get_logins_per_1h(self, _):
        """Get successful logins per hour for the last 24 hours"""
        user = self.context["user"]
        return get_events_per_1h(action=EventAction.LOGIN, user__pk=user.pk)

    @extend_schema_field(CoordinateSerializer(many=True))
    def get_logins_failed_per_1h(self, _):
        """Get failed logins per hour for the last 24 hours"""
        user = self.context["user"]
        return get_events_per_1h(action=EventAction.LOGIN_FAILED, context__username=user.username)

    @extend_schema_field(CoordinateSerializer(many=True))
    def get_authorizations_per_1h(self, _):
        """Get failed logins per hour for the last 24 hours"""
        user = self.context["user"]
        return get_events_per_1h(action=EventAction.AUTHORIZE_APPLICATION, user__pk=user.pk)


class UsersFilter(FilterSet):
    """Filter for users"""

    attributes = CharFilter(
        field_name="attributes",
        lookup_expr="",
        label="Attributes",
        method="filter_attributes",
    )

    is_superuser = BooleanFilter(field_name="ak_groups", lookup_expr="is_superuser")

    # pylint: disable=unused-argument
    def filter_attributes(self, queryset, name, value):
        """Filter attributes by query args"""
        try:
            value = loads(value)
        except ValueError:
            raise ValidationError(detail="filter: failed to parse JSON")
        if not isinstance(value, dict):
            raise ValidationError(detail="filter: value must be key:value mapping")
        qs = {}
        for key, _value in value.items():
            qs[f"attributes__{key}"] = _value
        return queryset.filter(**qs)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "name",
            "is_active",
            "is_superuser",
            "attributes",
        ]


class UserViewSet(UsedByMixin, ModelViewSet):
    """User Viewset"""

    queryset = User.objects.none()
    serializer_class = UserSerializer
    search_fields = ["username", "name", "is_active", "email"]
    filterset_class = UsersFilter

    def get_queryset(self):  # pragma: no cover
        return User.objects.all().exclude(pk=get_anonymous_user().pk)

    @extend_schema(responses={200: SessionUserSerializer(many=False)})
    @action(detail=False, pagination_class=None, filter_backends=[])
    # pylint: disable=invalid-name
    def me(self, request: Request) -> Response:
        """Get information about current user"""
        serializer = SessionUserSerializer(data={"user": UserSelfSerializer(request.user).data})
        if SESSION_IMPERSONATE_USER in request._request.session:
            serializer.initial_data["original"] = UserSelfSerializer(
                request._request.session[SESSION_IMPERSONATE_ORIGINAL_USER]
            ).data
        serializer.is_valid()
        return Response(serializer.data)

    @extend_schema(request=UserSelfSerializer, responses={200: SessionUserSerializer(many=False)})
    @action(
        methods=["PUT"],
        detail=False,
        pagination_class=None,
        filter_backends=[],
        permission_classes=[IsAuthenticated],
    )
    def update_self(self, request: Request) -> Response:
        """Allow users to change information on their own profile"""
        data = UserSelfSerializer(instance=User.objects.get(pk=request.user.pk), data=request.data)
        if not data.is_valid():
            return Response(data.errors)
        new_user = data.save()
        # If we're impersonating, we need to update that user object
        # since it caches the full object
        if SESSION_IMPERSONATE_USER in request.session:
            request.session[SESSION_IMPERSONATE_USER] = new_user
        return self.me(request)

    @permission_required("authentik_core.view_user", ["authentik_events.view_event"])
    @extend_schema(responses={200: UserMetricsSerializer(many=False)})
    @action(detail=True, pagination_class=None, filter_backends=[])
    # pylint: disable=invalid-name, unused-argument
    def metrics(self, request: Request, pk: int) -> Response:
        """User metrics per 1h"""
        user: User = self.get_object()
        serializer = UserMetricsSerializer(True)
        serializer.context["user"] = user
        return Response(serializer.data)

    @permission_required("authentik_core.reset_user_password")
    @extend_schema(
        responses={
            "200": LinkSerializer(many=False),
            "404": LinkSerializer(many=False),
        },
    )
    @action(detail=True, pagination_class=None, filter_backends=[])
    # pylint: disable=invalid-name, unused-argument
    def recovery(self, request: Request, pk: int) -> Response:
        """Create a temporary link that a user can use to recover their accounts"""
        tenant: Tenant = request._request.tenant
        # Check that there is a recovery flow, if not return an error
        flow = tenant.flow_recovery
        if not flow:
            return Response({"link": ""}, status=404)
        user: User = self.get_object()
        token, __ = Token.objects.get_or_create(
            identifier=f"{user.uid}-password-reset",
            user=user,
            intent=TokenIntents.INTENT_RECOVERY,
        )
        querystring = urlencode({"token": token.key})
        link = request.build_absolute_uri(
            reverse_lazy("authentik_core:if-flow", kwargs={"flow_slug": flow.slug})
            + f"?{querystring}"
        )
        return Response({"link": link})

    def _filter_queryset_for_list(self, queryset: QuerySet) -> QuerySet:
        """Custom filter_queryset method which ignores guardian, but still supports sorting"""
        for backend in list(self.filter_backends):
            if backend == ObjectPermissionsFilter:
                continue
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    def filter_queryset(self, queryset):
        if self.request.user.has_perm("authentik_core.view_user"):
            return self._filter_queryset_for_list(queryset)
        return super().filter_queryset(queryset)
