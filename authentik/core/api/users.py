"""User API Views"""

from datetime import datetime, timedelta
from hashlib import sha256
from json import loads
from typing import Any

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import AnonymousUser, Permission
from django.contrib.sessions.backends.cache import KEY_PREFIX
from django.core.cache import cache
from django.db.models.functions import ExtractHour
from django.db.transaction import atomic
from django.db.utils import IntegrityError
from django.urls import reverse_lazy
from django.utils.http import urlencode
from django.utils.text import slugify
from django.utils.timezone import now
from django.utils.translation import gettext as _
from django_filters.filters import (
    BooleanFilter,
    CharFilter,
    ModelMultipleChoiceFilter,
    MultipleChoiceFilter,
    UUIDFilter,
)
from django_filters.filterset import FilterSet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_field,
    inline_serializer,
)
from guardian.shortcuts import get_objects_for_user
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.fields import (
    BooleanField,
    CharField,
    ChoiceField,
    DateTimeField,
    IntegerField,
    ListField,
    SerializerMethodField,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import (
    ListSerializer,
    PrimaryKeyRelatedField,
)
from rest_framework.validators import UniqueValidator
from rest_framework.viewsets import ModelViewSet
from structlog.stdlib import get_logger

from authentik.admin.api.metrics import CoordinateSerializer
from authentik.blueprints.v1.importer import SERIALIZER_CONTEXT_BLUEPRINT
from authentik.brands.models import Brand
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import (
    JSONDictField,
    LinkSerializer,
    ModelSerializer,
    PassiveSerializer,
)
from authentik.core.middleware import (
    SESSION_KEY_IMPERSONATE_ORIGINAL_USER,
    SESSION_KEY_IMPERSONATE_USER,
)
from authentik.core.models import (
    USER_ATTRIBUTE_TOKEN_EXPIRING,
    USER_PATH_SERVICE_ACCOUNT,
    AuthenticatedSession,
    Group,
    Token,
    TokenIntents,
    User,
    UserTypes,
)
from authentik.events.models import Event, EventAction
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import FlowToken
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlanner
from authentik.flows.views.executor import QS_KEY_TOKEN
from authentik.lib.avatars import get_avatar
from authentik.lib.utils.time import timedelta_from_string, timedelta_string_validator
from authentik.rbac.decorators import permission_required
from authentik.rbac.models import get_permission_choices
from authentik.stages.email.models import EmailStage
from authentik.stages.email.tasks import send_mails
from authentik.stages.email.utils import TemplateEmailMessage

LOGGER = get_logger()


class UserGroupSerializer(ModelSerializer):
    """Simplified Group Serializer for user's groups"""

    attributes = JSONDictField(required=False)
    parent_name = CharField(source="parent.name", read_only=True, allow_null=True)

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
    avatar = SerializerMethodField()
    attributes = JSONDictField(required=False)
    groups = PrimaryKeyRelatedField(
        allow_empty=True,
        many=True,
        source="ak_groups",
        queryset=Group.objects.all().order_by("name"),
        default=list,
    )
    groups_obj = SerializerMethodField(allow_null=True)
    uid = CharField(read_only=True)
    username = CharField(
        max_length=150,
        validators=[UniqueValidator(queryset=User.objects.all().order_by("username"))],
    )

    @property
    def _should_include_groups(self) -> bool:
        request: Request = self.context.get("request", None)
        if not request:
            return True
        return str(request.query_params.get("include_groups", "true")).lower() == "true"

    @extend_schema_field(UserGroupSerializer(many=True))
    def get_groups_obj(self, instance: User) -> list[UserGroupSerializer] | None:
        if not self._should_include_groups:
            return None
        return UserGroupSerializer(instance.ak_groups, many=True).data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if SERIALIZER_CONTEXT_BLUEPRINT in self.context:
            self.fields["password"] = CharField(required=False, allow_null=True)
            self.fields["permissions"] = ListField(
                required=False, child=ChoiceField(choices=get_permission_choices())
            )

    def create(self, validated_data: dict) -> User:
        """If this serializer is used in the blueprint context, we allow for
        directly setting a password. However should be done via the `set_password`
        method instead of directly setting it like rest_framework."""
        password = validated_data.pop("password", None)
        permissions = Permission.objects.filter(
            codename__in=[x.split(".")[1] for x in validated_data.pop("permissions", [])]
        )
        validated_data["user_permissions"] = permissions
        instance: User = super().create(validated_data)
        self._set_password(instance, password)
        return instance

    def update(self, instance: User, validated_data: dict) -> User:
        """Same as `create` above, set the password directly if we're in a blueprint
        context"""
        password = validated_data.pop("password", None)
        permissions = Permission.objects.filter(
            codename__in=[x.split(".")[1] for x in validated_data.pop("permissions", [])]
        )
        validated_data["user_permissions"] = permissions
        instance = super().update(instance, validated_data)
        self._set_password(instance, password)
        return instance

    def _set_password(self, instance: User, password: str | None):
        """Set password of user if we're in a blueprint context, and if it's an empty
        string then use an unusable password"""
        if SERIALIZER_CONTEXT_BLUEPRINT in self.context and password:
            instance.set_password(password)
            instance.save()
        if len(instance.password) == 0:
            instance.set_unusable_password()
            instance.save()

    def get_avatar(self, user: User) -> str:
        """User's avatar, either a http/https URL or a data URI"""
        return get_avatar(user, self.context.get("request"))

    def validate_path(self, path: str) -> str:
        """Validate path"""
        if path[:1] == "/" or path[-1] == "/":
            raise ValidationError(_("No leading or trailing slashes allowed."))
        for segment in path.split("/"):
            if segment == "":
                raise ValidationError(_("No empty segments in user path allowed."))
        return path

    def validate_type(self, user_type: str) -> str:
        """Validate user type, internal_service_account is an internal value"""
        if (
            self.instance
            and self.instance.type == UserTypes.INTERNAL_SERVICE_ACCOUNT
            and user_type != UserTypes.INTERNAL_SERVICE_ACCOUNT.value
        ):
            raise ValidationError("Can't change internal service account to other user type.")
        if not self.instance and user_type == UserTypes.INTERNAL_SERVICE_ACCOUNT.value:
            raise ValidationError("Setting a user to internal service account is not allowed.")
        return user_type

    def validate(self, attrs: dict) -> dict:
        if self.instance and self.instance.type == UserTypes.INTERNAL_SERVICE_ACCOUNT:
            raise ValidationError("Can't modify internal service account users")
        return super().validate(attrs)

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
            "type",
            "uuid",
            "password_change_date",
        ]
        extra_kwargs = {
            "name": {"allow_blank": True},
            "password_change_date": {"read_only": True},
        }


class UserSelfSerializer(ModelSerializer):
    """User Serializer for information a user can retrieve about themselves"""

    is_superuser = BooleanField(read_only=True)
    avatar = SerializerMethodField()
    groups = SerializerMethodField()
    uid = CharField(read_only=True)
    settings = SerializerMethodField()
    system_permissions = SerializerMethodField()

    def get_avatar(self, user: User) -> str:
        """User's avatar, either a http/https URL or a data URI"""
        return get_avatar(user, self.context.get("request"))

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
        for group in self.instance.all_groups().order_by("name"):
            yield {
                "name": group.name,
                "pk": group.pk,
            }

    def get_settings(self, user: User) -> dict[str, Any]:
        """Get user settings with brand and group settings applied"""
        return user.group_attributes(self._context["request"]).get("settings", {})

    def get_system_permissions(self, user: User) -> list[str]:
        """Get all system permissions assigned to the user"""
        return list(
            x.split(".", maxsplit=1)[1]
            for x in user.get_all_permissions()
            if x.startswith("authentik_rbac")
        )

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
            "type",
            "system_permissions",
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
    uuid = UUIDFilter(field_name="uuid")

    path = CharFilter(field_name="path")
    path_startswith = CharFilter(field_name="path", lookup_expr="startswith")

    type = MultipleChoiceFilter(choices=UserTypes.choices, field_name="type")

    groups_by_name = ModelMultipleChoiceFilter(
        field_name="ak_groups__name",
        to_field_name="name",
        queryset=Group.objects.all().order_by("name"),
    )
    groups_by_pk = ModelMultipleChoiceFilter(
        field_name="ak_groups",
        queryset=Group.objects.all().order_by("name"),
    )

    def filter_attributes(self, queryset, name, value):
        """Filter attributes by query args"""
        try:
            value = loads(value)
        except ValueError:
            raise ValidationError(detail="filter: failed to parse JSON") from None
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
            "type",
        ]


class UserViewSet(UsedByMixin, ModelViewSet):
    """User Viewset"""

    queryset = User.objects.none()
    ordering = ["username"]
    serializer_class = UserSerializer
    search_fields = ["username", "name", "is_active", "email", "uuid", "attributes"]
    filterset_class = UsersFilter

    def get_queryset(self):
        base_qs = User.objects.all().exclude_anonymous()
        if self.serializer_class(context={"request": self.request})._should_include_groups:
            base_qs = base_qs.prefetch_related("ak_groups")
        return base_qs

    @extend_schema(
        parameters=[
            OpenApiParameter("include_groups", bool, default=True),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def _create_recovery_link(self, expires: datetime) -> tuple[str, Token]:
        """Create a recovery link (when the current brand has a recovery flow set),
        that can either be shown to an admin or sent to the user directly"""
        brand: Brand = self.request._request.brand
        # Check that there is a recovery flow, if not return an error
        flow = brand.flow_recovery
        if not flow:
            raise ValidationError(
                {"non_field_errors": [_("Recovery flow is not set for this brand.")]}
            )
        # Mimic an unauthenticated user navigating the recovery flow
        user: User = self.get_object()
        self.request._request.user = AnonymousUser()
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
            raise ValidationError(
                {"non_field_errors": [_("Recovery flow is not applicable to this user.")]}
            ) from None
        token = FlowToken.objects.create(
            identifier=f"{user.uid}-password-reset-{sha256(str(datetime.now()).encode('UTF-8')).hexdigest()[:8]}",
            user=user,
            flow=flow,
            _plan=FlowToken.pickle(plan),
            expires=expires,
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
                    type=UserTypes.SERVICE_ACCOUNT,
                    attributes={USER_ATTRIBUTE_TOKEN_EXPIRING: expiring},
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
    @action(detail=True, methods=["POST"], permission_classes=[])
    def set_password(self, request: Request, pk: int) -> Response:
        """Set password for user"""
        user: User = self.get_object()
        try:
            user.set_password(request.data.get("password"), request=request)
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
        parameters=[
            OpenApiParameter(
                name="email_stage",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="token_duration",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                required=True,
            ),
        ],
        responses={
            "200": LinkSerializer(many=False),
        },
        request=None,
    )
    @action(detail=True, pagination_class=None, filter_backends=[], methods=["POST"])
    def recovery_link(self, request: Request, pk: int) -> Response:
        """Create a temporary link that a user can use to recover their accounts"""
        token_duration = request.query_params.get("token_duration", "")
        timedelta_string_validator(token_duration)
        expires = now() + timedelta_from_string(token_duration)
        link, token = self._create_recovery_link(expires)

        if email_stage := request.query_params.get("email_stage"):
            for_user: User = self.get_object()
            if for_user.email == "":
                LOGGER.debug("User doesn't have an email address")
                raise ValidationError(
                    {"non_field_errors": [_("User does not have an email address set.")]}
                )

            # Lookup the email stage to assure the current user can access it
            stages = get_objects_for_user(
                request.user, "authentik_stages_email.view_emailstage"
            ).filter(pk=email_stage)
            if not stages.exists():
                if stages := EmailStage.objects.filter(pk=email_stage).exists():
                    raise ValidationError(
                        {"non_field_errors": [_("User has no permissions to this Email stage.")]}
                    )
                else:
                    raise ValidationError(
                        {"non_field_errors": [_("The given Email stage does not exist.")]}
                    )
            email_stage: EmailStage = stages.first()
            message = TemplateEmailMessage(
                subject=_(email_stage.subject),
                to=[(for_user.name, for_user.email)],
                template_name=email_stage.template,
                language=for_user.locale(request),
                template_context={
                    "url": link,
                    "user": for_user,
                    "expires": token.expires,
                },
            )
            send_mails(email_stage, message)

        return Response({"link": link})

    @permission_required("authentik_core.impersonate")
    @extend_schema(
        request=inline_serializer(
            "ImpersonationSerializer",
            {
                "reason": CharField(required=True),
            },
        ),
        responses={
            "204": OpenApiResponse(description="Successfully started impersonation"),
            "401": OpenApiResponse(description="Access denied"),
        },
    )
    @action(detail=True, methods=["POST"], permission_classes=[])
    def impersonate(self, request: Request, pk: int) -> Response:
        """Impersonate a user"""
        if not request.tenant.impersonation:
            LOGGER.debug("User attempted to impersonate", user=request.user)
            return Response(status=401)
        user_to_be = self.get_object()
        reason = request.data.get("reason", "")
        # Check both object-level perms and global perms
        if not request.user.has_perm(
            "authentik_core.impersonate", user_to_be
        ) and not request.user.has_perm("authentik_core.impersonate"):
            LOGGER.debug("User attempted to impersonate without permissions", user=request.user)
            return Response(status=401)
        if user_to_be.pk == self.request.user.pk:
            LOGGER.debug("User attempted to impersonate themselves", user=request.user)
            return Response(status=401)
        if not reason and request.tenant.impersonation_require_reason:
            LOGGER.debug(
                "User attempted to impersonate without providing a reason", user=request.user
            )
            return Response(status=401)

        request.session[SESSION_KEY_IMPERSONATE_ORIGINAL_USER] = request.user
        request.session[SESSION_KEY_IMPERSONATE_USER] = user_to_be

        Event.new(EventAction.IMPERSONATION_STARTED, reason=reason).from_http(request, user_to_be)

        return Response(status=201)

    @extend_schema(
        request=OpenApiTypes.NONE,
        responses={
            "204": OpenApiResponse(description="Successfully started impersonation"),
        },
    )
    @action(detail=False, methods=["GET"])
    def impersonate_end(self, request: Request) -> Response:
        """End Impersonation a user"""
        if (
            SESSION_KEY_IMPERSONATE_USER not in request.session
            or SESSION_KEY_IMPERSONATE_ORIGINAL_USER not in request.session
        ):
            LOGGER.debug("Can't end impersonation", user=request.user)
            return Response(status=204)

        original_user = request.session[SESSION_KEY_IMPERSONATE_ORIGINAL_USER]

        del request.session[SESSION_KEY_IMPERSONATE_USER]
        del request.session[SESSION_KEY_IMPERSONATE_ORIGINAL_USER]

        Event.new(EventAction.IMPERSONATION_ENDED).from_http(request, original_user)

        return Response(status=204)

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
