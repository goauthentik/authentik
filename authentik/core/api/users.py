"""User API Views"""
from datetime import timedelta
from json import loads
from typing import Any, Optional

from django.contrib.auth import update_session_auth_hash
from django.contrib.sessions.backends.cache import KEY_PREFIX
from django.core.cache import cache
from django.db.models.functions import ExtractHour
from django.db.models.query import QuerySet
from django.db.transaction import atomic
from django.db.utils import IntegrityError
from django.urls import reverse_lazy
from django.utils.http import urlencode
from django.utils.text import slugify
from django.utils.timezone import now
from django.utils.translation import gettext as _
from django_filters.filters import BooleanFilter, CharFilter, ModelMultipleChoiceFilter
from django_filters.filterset import FilterSet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_field,
    inline_serializer,
)
from guardian.shortcuts import get_anonymous_user, get_objects_for_user
from rest_framework.decorators import action
from rest_framework.fields import (
    CharField,
    IntegerField,
    JSONField,
    ListField,
    SerializerMethodField,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import (
    BooleanField,
    DateTimeField,
    ListSerializer,
    ModelSerializer,
    PrimaryKeyRelatedField,
    ValidationError,
)
from rest_framework.validators import UniqueValidator
from rest_framework.viewsets import ModelViewSet
from rest_framework_guardian.filters import ObjectPermissionsFilter
from structlog.stdlib import get_logger

from authentik.admin.api.metrics import CoordinateSerializer
from authentik.api.decorators import permission_required
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import LinkSerializer, PassiveSerializer, is_dict
from authentik.core.middleware import (
    SESSION_KEY_IMPERSONATE_ORIGINAL_USER,
    SESSION_KEY_IMPERSONATE_USER,
)
from authentik.core.models import (
    USER_ATTRIBUTE_SA,
    USER_ATTRIBUTE_TOKEN_EXPIRING,
    USER_PATH_SERVICE_ACCOUNT,
    AuthenticatedSession,
    Group,
    Token,
    TokenIntents,
    User,
)
from authentik.events.models import EventAction
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import FlowToken
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlanner
from authentik.flows.views.executor import QS_KEY_TOKEN
from authentik.stages.email.models import EmailStage
from authentik.stages.email.tasks import send_mails
from authentik.stages.email.utils import TemplateEmailMessage
from authentik.tenants.models import Tenant

LOGGER = get_logger()


class UserGroupSerializer(ModelSerializer):
    """Simplified Group Serializer for user's groups"""

    attributes = JSONField(required=False)
    parent_name = CharField(source="parent.name", read_only=True)

    class Meta:
        model = Group
        fields = [
            "pk",
            "num_pk",
            "name",
            "is_superuser",
            "parent",
            "parent_name",
            "attributes",
        ]


class UserSerializer(ModelSerializer):
    """User Serializer"""

    is_superuser = BooleanField(read_only=True)
    avatar = CharField(read_only=True)
    attributes = JSONField(validators=[is_dict], required=False)
    groups = PrimaryKeyRelatedField(
        allow_empty=True, many=True, source="ak_groups", queryset=Group.objects.all(), default=list
    )
    groups_obj = ListSerializer(child=UserGroupSerializer(), read_only=True, source="ak_groups")
    uid = CharField(read_only=True)
    username = CharField(max_length=150, validators=[UniqueValidator(queryset=User.objects.all())])

    def validate_path(self, path: str) -> str:
        """Validate path"""
        if path[:1] == "/" or path[-1] == "/":
            raise ValidationError(_("No leading or trailing slashes allowed."))
        for segment in path.split("/"):
            if segment == "":
                raise ValidationError(_("No empty segments in user path allowed."))
        return path

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
            "groups_obj",
            "email",
            "avatar",
            "attributes",
            "uid",
            "path",
        ]
        extra_kwargs = {
            "name": {"allow_blank": True},
        }


class UserSelfSerializer(ModelSerializer):
    """User Serializer for information a user can retrieve about themselves"""

    is_superuser = BooleanField(read_only=True)
    avatar = CharField(read_only=True)
    groups = SerializerMethodField()
    uid = CharField(read_only=True)
    settings = SerializerMethodField()

    @extend_schema_field(
        ListSerializer(
            child=inline_serializer(
                "UserSelfGroups",
                {"name": CharField(read_only=True), "pk": CharField(read_only=True)},
            )
        )
    )
    def get_groups(self, _: User):
        """Return only the group names a user is member of"""
        for group in self.instance.ak_groups.all():
            yield {
                "name": group.name,
                "pk": group.pk,
            }

    def get_settings(self, user: User) -> dict[str, Any]:
        """Get user settings with tenant and group settings applied"""
        return user.group_attributes(self._context["request"]).get("settings", {})

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
            "settings",
        ]
        extra_kwargs = {
            "is_active": {"read_only": True},
            "name": {"allow_blank": True},
        }


class SessionUserSerializer(PassiveSerializer):
    """Response for the /user/me endpoint, returns the currently active user (as `user` property)
    and, if this user is being impersonated, the original user in the `original` property."""

    user = UserSelfSerializer()
    original = UserSelfSerializer(required=False)


class UserMetricsSerializer(PassiveSerializer):
    """User Metrics"""

    logins = SerializerMethodField()
    logins_failed = SerializerMethodField()
    authorizations = SerializerMethodField()

    @extend_schema_field(CoordinateSerializer(many=True))
    def get_logins(self, _):
        """Get successful logins per 8 hours for the last 7 days"""
        user = self.context["user"]
        request = self.context["request"]
        return (
            get_objects_for_user(request.user, "authentik_events.view_event").filter(
                action=EventAction.LOGIN, user__pk=user.pk
            )
            # 3 data points per day, so 8 hour spans
            .get_events_per(timedelta(days=7), ExtractHour, 7 * 3)
        )

    @extend_schema_field(CoordinateSerializer(many=True))
    def get_logins_failed(self, _):
        """Get failed logins per 8 hours for the last 7 days"""
        user = self.context["user"]
        request = self.context["request"]
        return (
            get_objects_for_user(request.user, "authentik_events.view_event").filter(
                action=EventAction.LOGIN_FAILED, context__username=user.username
            )
            # 3 data points per day, so 8 hour spans
            .get_events_per(timedelta(days=7), ExtractHour, 7 * 3)
        )

    @extend_schema_field(CoordinateSerializer(many=True))
    def get_authorizations(self, _):
        """Get failed logins per 8 hours for the last 7 days"""
        user = self.context["user"]
        request = self.context["request"]
        return (
            get_objects_for_user(request.user, "authentik_events.view_event").filter(
                action=EventAction.AUTHORIZE_APPLICATION, user__pk=user.pk
            )
            # 3 data points per day, so 8 hour spans
            .get_events_per(timedelta(days=7), ExtractHour, 7 * 3)
        )


class UsersFilter(FilterSet):
    """Filter for users"""

    attributes = CharFilter(
        field_name="attributes",
        lookup_expr="",
        label="Attributes",
        method="filter_attributes",
    )

    is_superuser = BooleanFilter(field_name="ak_groups", lookup_expr="is_superuser")
    uuid = CharFilter(field_name="uuid")

    path = CharFilter(
        field_name="path",
    )
    path_startswith = CharFilter(field_name="path", lookup_expr="startswith")

    groups_by_name = ModelMultipleChoiceFilter(
        field_name="ak_groups__name",
        to_field_name="name",
        queryset=Group.objects.all(),
    )
    groups_by_pk = ModelMultipleChoiceFilter(
        field_name="ak_groups",
        queryset=Group.objects.all(),
    )

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
        try:
            _ = len(queryset.filter(**qs))
            return queryset.filter(**qs)
        except ValueError:
            return queryset

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "name",
            "is_active",
            "is_superuser",
            "attributes",
            "groups_by_name",
            "groups_by_pk",
        ]


class UserViewSet(UsedByMixin, ModelViewSet):
    """User Viewset"""

    queryset = User.objects.none()
    ordering = ["username"]
    serializer_class = UserSerializer
    search_fields = ["username", "name", "is_active", "email", "uuid"]
    filterset_class = UsersFilter

    def get_queryset(self):  # pragma: no cover
        return User.objects.all().exclude(pk=get_anonymous_user().pk)

    def _create_recovery_link(self) -> tuple[Optional[str], Optional[Token]]:
        """Create a recovery link (when the current tenant has a recovery flow set),
        that can either be shown to an admin or sent to the user directly"""
        tenant: Tenant = self.request._request.tenant
        # Check that there is a recovery flow, if not return an error
        flow = tenant.flow_recovery
        if not flow:
            LOGGER.debug("No recovery flow set")
            return None, None
        user: User = self.get_object()
        planner = FlowPlanner(flow)
        planner.allow_empty_flows = True
        try:
            plan = planner.plan(
                self.request._request,
                {
                    PLAN_CONTEXT_PENDING_USER: user,
                },
            )
        except FlowNonApplicableException:
            LOGGER.warning("Recovery flow not applicable to user")
            return None, None
        token, __ = FlowToken.objects.update_or_create(
            identifier=f"{user.uid}-password-reset",
            defaults={
                "user": user,
                "flow": flow,
                "_plan": FlowToken.pickle(plan),
            },
        )
        querystring = urlencode({QS_KEY_TOKEN: token.key})
        link = self.request.build_absolute_uri(
            reverse_lazy("authentik_core:if-flow", kwargs={"flow_slug": flow.slug})
            + f"?{querystring}"
        )
        return link, token

    @permission_required(None, ["authentik_core.add_user", "authentik_core.add_token"])
    @extend_schema(
        request=inline_serializer(
            "UserServiceAccountSerializer",
            {
                "name": CharField(required=True),
                "create_group": BooleanField(default=False),
                "expiring": BooleanField(default=True),
                "expires": DateTimeField(
                    required=False,
                    help_text="If not provided, valid for 360 days",
                ),
            },
        ),
        responses={
            200: inline_serializer(
                "UserServiceAccountResponse",
                {
                    "username": CharField(required=True),
                    "token": CharField(required=True),
                    "user_uid": CharField(required=True),
                    "user_pk": IntegerField(required=True),
                    "group_pk": CharField(required=False),
                },
            )
        },
    )
    @action(detail=False, methods=["POST"], pagination_class=None, filter_backends=[])
    def service_account(self, request: Request) -> Response:
        """Create a new user account that is marked as a service account"""
        username = request.data.get("name")
        create_group = request.data.get("create_group", False)
        expiring = request.data.get("expiring", True)
        expires = request.data.get("expires", now() + timedelta(days=360))

        with atomic():
            try:
                user: User = User.objects.create(
                    username=username,
                    name=username,
                    attributes={USER_ATTRIBUTE_SA: True, USER_ATTRIBUTE_TOKEN_EXPIRING: expiring},
                    path=USER_PATH_SERVICE_ACCOUNT,
                )
                user.set_unusable_password()
                user.save()

                response = {
                    "username": user.username,
                    "user_uid": user.uid,
                    "user_pk": user.pk,
                }
                if create_group and self.request.user.has_perm("authentik_core.add_group"):
                    group = Group.objects.create(
                        name=username,
                    )
                    group.users.add(user)
                    response["group_pk"] = str(group.pk)
                token = Token.objects.create(
                    identifier=slugify(f"service-account-{username}-password"),
                    intent=TokenIntents.INTENT_APP_PASSWORD,
                    user=user,
                    expires=expires,
                    expiring=expiring,
                )
                response["token"] = token.key
                return Response(response)
            except IntegrityError as exc:
                return Response(data={"non_field_errors": [str(exc)]}, status=400)

    @extend_schema(responses={200: SessionUserSerializer(many=False)})
    @action(url_path="me", url_name="me", detail=False, pagination_class=None, filter_backends=[])
    def user_me(self, request: Request) -> Response:
        """Get information about current user"""
        context = {"request": request}
        serializer = SessionUserSerializer(
            data={"user": UserSelfSerializer(instance=request.user, context=context).data}
        )
        if SESSION_KEY_IMPERSONATE_USER in request._request.session:
            serializer.initial_data["original"] = UserSelfSerializer(
                instance=request._request.session[SESSION_KEY_IMPERSONATE_ORIGINAL_USER],
                context=context,
            ).data
        self.request.session.modified = True
        return Response(serializer.initial_data)

    @permission_required("authentik_core.reset_user_password")
    @extend_schema(
        request=inline_serializer(
            "UserPasswordSetSerializer",
            {
                "password": CharField(required=True),
            },
        ),
        responses={
            204: OpenApiResponse(description="Successfully changed password"),
            400: OpenApiResponse(description="Bad request"),
        },
    )
    @action(detail=True, methods=["POST"])
    def set_password(self, request: Request, pk: int) -> Response:
        """Set password for user"""
        user: User = self.get_object()
        try:
            user.set_password(request.data.get("password"))
            user.save()
        except (ValidationError, IntegrityError) as exc:
            LOGGER.debug("Failed to set password", exc=exc)
            return Response(status=400)
        if user.pk == request.user.pk and SESSION_KEY_IMPERSONATE_USER not in self.request.session:
            LOGGER.debug("Updating session hash after password change")
            update_session_auth_hash(self.request, user)
        return Response(status=204)

    @permission_required("authentik_core.view_user", ["authentik_events.view_event"])
    @extend_schema(responses={200: UserMetricsSerializer(many=False)})
    @action(detail=True, pagination_class=None, filter_backends=[])
    def metrics(self, request: Request, pk: int) -> Response:
        """User metrics per 1h"""
        user: User = self.get_object()
        serializer = UserMetricsSerializer(instance={})
        serializer.context["user"] = user
        serializer.context["request"] = request
        return Response(serializer.data)

    @permission_required("authentik_core.reset_user_password")
    @extend_schema(
        responses={
            "200": LinkSerializer(many=False),
            "404": LinkSerializer(many=False),
        },
    )
    @action(detail=True, pagination_class=None, filter_backends=[])
    def recovery(self, request: Request, pk: int) -> Response:
        """Create a temporary link that a user can use to recover their accounts"""
        link, _ = self._create_recovery_link()
        if not link:
            LOGGER.debug("Couldn't create token")
            return Response({"link": ""}, status=404)
        return Response({"link": link})

    @permission_required("authentik_core.reset_user_password")
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="email_stage",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                required=True,
            )
        ],
        responses={
            "204": OpenApiResponse(description="Successfully sent recover email"),
            "404": OpenApiResponse(description="Bad request"),
        },
    )
    @action(detail=True, pagination_class=None, filter_backends=[])
    def recovery_email(self, request: Request, pk: int) -> Response:
        """Create a temporary link that a user can use to recover their accounts"""
        for_user: User = self.get_object()
        if for_user.email == "":
            LOGGER.debug("User doesn't have an email address")
            return Response(status=404)
        link, token = self._create_recovery_link()
        if not link:
            LOGGER.debug("Couldn't create token")
            return Response(status=404)
        # Lookup the email stage to assure the current user can access it
        stages = get_objects_for_user(
            request.user, "authentik_stages_email.view_emailstage"
        ).filter(pk=request.query_params.get("email_stage"))
        if not stages.exists():
            LOGGER.debug("Email stage does not exist/user has no permissions")
            return Response(status=404)
        email_stage: EmailStage = stages.first()
        message = TemplateEmailMessage(
            subject=_(email_stage.subject),
            to=[for_user.email],
            template_name=email_stage.template,
            language=for_user.locale(request),
            template_context={
                "url": link,
                "user": for_user,
                "expires": token.expires,
            },
        )
        send_mails(email_stage, message)
        return Response(status=204)

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

    @extend_schema(
        responses={
            200: inline_serializer(
                "UserPathSerializer", {"paths": ListField(child=CharField(), read_only=True)}
            )
        },
        parameters=[
            OpenApiParameter(
                name="search",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
            )
        ],
    )
    @action(detail=False, pagination_class=None)
    def paths(self, request: Request) -> Response:
        """Get all user paths"""
        return Response(
            data={
                "paths": list(
                    self.filter_queryset(self.get_queryset())
                    .values("path")
                    .distinct()
                    .order_by("path")
                    .values_list("path", flat=True)
                )
            }
        )

    def partial_update(self, request: Request, *args, **kwargs) -> Response:
        response = super().partial_update(request, *args, **kwargs)
        instance: User = self.get_object()
        if not instance.is_active:
            sessions = AuthenticatedSession.objects.filter(user=instance)
            session_ids = sessions.values_list("session_key", flat=True)
            cache.delete_many(f"{KEY_PREFIX}{session}" for session in session_ids)
            sessions.delete()
            LOGGER.debug("Deleted user's sessions", user=instance.username)
        return response
