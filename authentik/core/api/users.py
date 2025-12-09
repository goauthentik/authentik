"""User API Views"""

from datetime import timedelta
from json import loads
from typing import Any

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import AnonymousUser, Permission
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
    IsoDateTimeFilter,
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
from rest_framework.authentication import SessionAuthentication
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
    UUIDField,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import (
    ListSerializer,
    PrimaryKeyRelatedField,
)
from rest_framework.validators import UniqueValidator
from rest_framework.viewsets import ModelViewSet
from structlog.stdlib import get_logger

from authentik.api.authentication import TokenAuthentication
from authentik.api.validation import validate
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
    Group,
    Session,
    Token,
    TokenIntents,
    User,
    UserTypes,
    default_token_duration,
)
from authentik.endpoints.connectors.agent.auth import AgentAuth
from authentik.events.models import Event, EventAction
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import FlowToken
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlanner
from authentik.flows.views.executor import QS_KEY_TOKEN
from authentik.lib.avatars import get_avatar
from authentik.lib.utils.reflection import ConditionalInheritance
from authentik.lib.utils.time import timedelta_from_string, timedelta_string_validator
from authentik.rbac.api.roles import RoleSerializer
from authentik.rbac.decorators import permission_required
from authentik.rbac.models import Role, get_permission_choices
from authentik.stages.email.flow import pickle_flow_token_for_email
from authentik.stages.email.models import EmailStage
from authentik.stages.email.tasks import send_mails
from authentik.stages.email.utils import TemplateEmailMessage

LOGGER = get_logger()


class ParamUserSerializer(PassiveSerializer):
    """Partial serializer for query parameters to select a user"""

    user = PrimaryKeyRelatedField(queryset=User.objects.all().exclude_anonymous(), required=False)


class PartialGroupSerializer(ModelSerializer):
    """Partial Group Serializer, does not include child relations."""

    attributes = JSONDictField(required=False)

    class Meta:
        model = Group
        fields = [
            "pk",
            "num_pk",
            "name",
            "is_superuser",
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
        queryset=Group.objects.all().order_by("name"),
        default=list,
    )
    groups_obj = SerializerMethodField(allow_null=True)
    roles = PrimaryKeyRelatedField(
        allow_empty=True,
        many=True,
        queryset=Role.objects.all().order_by("name"),
        default=list,
    )
    roles_obj = SerializerMethodField(allow_null=True)
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

    @property
    def _should_include_roles(self) -> bool:
        request: Request = self.context.get("request", None)
        if not request:
            return True
        return str(request.query_params.get("include_roles", "true")).lower() == "true"

    @extend_schema_field(PartialGroupSerializer(many=True))
    def get_groups_obj(self, instance: User) -> list[PartialGroupSerializer] | None:
        if not self._should_include_groups:
            return None
        return PartialGroupSerializer(instance.groups, many=True).data

    @extend_schema_field(RoleSerializer(many=True))
    def get_roles_obj(self, instance: User) -> list[RoleSerializer] | None:
        if not self._should_include_roles:
            return None
        return RoleSerializer(instance.roles, many=True).data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if SERIALIZER_CONTEXT_BLUEPRINT in self.context:
            self.fields["password"] = CharField(required=False, allow_null=True)
            self.fields["password_hash"] = CharField(required=False, allow_null=True)
            self.fields["permissions"] = ListField(
                required=False,
                child=ChoiceField(choices=get_permission_choices()),
            )

    def create(self, validated_data: dict) -> User:
        """If this serializer is used in the blueprint context, we allow for
        directly setting a password. However should be done via the `set_password`
        method instead of directly setting it like rest_framework."""
        password = validated_data.pop("password", None)
        password_hash = validated_data.pop("password_hash", None)
        perms_qs = Permission.objects.filter(
            codename__in=[x.split(".")[1] for x in validated_data.pop("permissions", [])]
        ).values_list("content_type__app_label", "codename")
        perms_list = [f"{ct}.{name}" for ct, name in list(perms_qs)]
        instance: User = super().create(validated_data)
        self._set_password(instance, password, password_hash)
        instance.assign_perms_to_managed_role(perms_list)
        return instance

    def update(self, instance: User, validated_data: dict) -> User:
        """Same as `create` above, set the password directly if we're in a blueprint
        context"""
        password = validated_data.pop("password", None)
        password_hash = validated_data.pop("password_hash", None)
        perms_qs = Permission.objects.filter(
            codename__in=[x.split(".")[1] for x in validated_data.pop("permissions", [])]
        ).values_list("content_type__app_label", "codename")
        perms_list = [f"{ct}.{name}" for ct, name in list(perms_qs)]
        instance = super().update(instance, validated_data)
        self._set_password(instance, password, password_hash)
        instance.assign_perms_to_managed_role(perms_list)
        return instance

    def _set_password(self, instance: User, password: str | None, password_hash: str | None = None):
        """Set password of user if we're in a blueprint context, and if it's an empty
        string then use an unusable password. Supports both plaintext password and
        pre-hashed password via password_hash parameter."""
        if SERIALIZER_CONTEXT_BLUEPRINT in self.context:
            # password_hash takes precedence over password
            if password_hash:
                # Validate the hash format before setting
                from django.contrib.auth.hashers import identify_hasher
                from rest_framework.exceptions import ValidationError

                try:
                    identify_hasher(password_hash)
                except ValueError as exc:
                    raise ValidationError(
                        f"Invalid password hash format. Must be a valid Django password hash: {exc}"
                    ) from exc

                # Directly set the hashed password without re-hashing
                instance.password = password_hash
                from django.utils.timezone import now

                instance.password_change_date = now()
                instance.save()
            elif password:
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
            raise ValidationError(_("Can't change internal service account to other user type."))
        if not self.instance and user_type == UserTypes.INTERNAL_SERVICE_ACCOUNT.value:
            raise ValidationError(_("Setting a user to internal service account is not allowed."))
        return user_type

    def validate(self, attrs: dict) -> dict:
        if self.instance and self.instance.type == UserTypes.INTERNAL_SERVICE_ACCOUNT:
            raise ValidationError(_("Can't modify internal service account users"))
        return super().validate(attrs)

    class Meta:
        model = User
        fields = [
            "pk",
            "username",
            "name",
            "is_active",
            "last_login",
            "date_joined",
            "is_superuser",
            "groups",
            "groups_obj",
            "roles",
            "roles_obj",
            "email",
            "avatar",
            "attributes",
            "uid",
            "path",
            "type",
            "uuid",
            "password_change_date",
            "last_updated",
        ]
        extra_kwargs = {
            "name": {"allow_blank": True},
            "date_joined": {"read_only": True},
            "password_change_date": {"read_only": True},
        }


class UserSelfSerializer(ModelSerializer):
    """User Serializer for information a user can retrieve about themselves"""

    is_superuser = BooleanField(read_only=True)
    avatar = SerializerMethodField()
    groups = SerializerMethodField()
    roles = SerializerMethodField()
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
                {
                    "name": CharField(read_only=True),
                    "pk": CharField(read_only=True),
                },
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

    @extend_schema_field(
        ListSerializer(
            child=inline_serializer(
                "UserSelfRoles",
                {
                    "name": CharField(read_only=True),
                    "pk": CharField(read_only=True),
                },
            )
        )
    )
    def get_roles(self, _: User):
        """Return only the roles a user is member of"""
        for role in self.instance.all_roles().order_by("name"):
            yield {
                "name": role.name,
                "pk": role.pk,
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
            "roles",
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
    and, if this user is being impersonated, the original user in the `original` property.
    """

    user = UserSelfSerializer()
    original = UserSelfSerializer(required=False)


class UserPasswordSetSerializer(PassiveSerializer):
    """Payload to set a users' password directly"""

    password = CharField(required=True)


class UserServiceAccountSerializer(PassiveSerializer):
    """Payload to create a service account"""

    name = CharField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all().order_by("username"))],
    )
    create_group = BooleanField(default=False)
    expiring = BooleanField(default=True)
    expires = DateTimeField(
        required=False,
        help_text="If not provided, valid for 360 days",
    )


class UserRecoveryLinkSerializer(PassiveSerializer):
    """Payload to create a recovery link"""

    token_duration = CharField(required=False)


class UserRecoveryEmailSerializer(UserRecoveryLinkSerializer):
    """Payload to create and email a recovery link"""

    email_stage = UUIDField()


class UsersFilter(FilterSet):
    """Filter for users"""

    attributes = CharFilter(
        field_name="attributes",
        lookup_expr="",
        label="Attributes",
        method="filter_attributes",
    )

    date_joined__lt = IsoDateTimeFilter(field_name="date_joined", lookup_expr="lt")
    date_joined = IsoDateTimeFilter(field_name="date_joined")
    date_joined__gt = IsoDateTimeFilter(field_name="date_joined", lookup_expr="gt")

    last_updated__lt = IsoDateTimeFilter(field_name="last_updated", lookup_expr="lt")
    last_updated = IsoDateTimeFilter(field_name="last_updated")
    last_updated__gt = IsoDateTimeFilter(field_name="last_updated", lookup_expr="gt")

    last_login__lt = IsoDateTimeFilter(field_name="last_login", lookup_expr="lt")
    last_login = IsoDateTimeFilter(field_name="last_login")
    last_login__gt = IsoDateTimeFilter(field_name="last_login", lookup_expr="gt")
    last_login__isnull = BooleanFilter(field_name="last_login", lookup_expr="isnull")

    is_superuser = BooleanFilter(field_name="groups", method="filter_is_superuser")
    uuid = UUIDFilter(field_name="uuid")

    path = CharFilter(field_name="path")
    path_startswith = CharFilter(field_name="path", lookup_expr="startswith")

    type = MultipleChoiceFilter(choices=UserTypes.choices, field_name="type")

    groups_by_name = ModelMultipleChoiceFilter(
        field_name="groups__name",
        to_field_name="name",
        queryset=Group.objects.all().order_by("name"),
    )
    groups_by_pk = ModelMultipleChoiceFilter(
        field_name="groups",
        queryset=Group.objects.all().order_by("name"),
    )

    roles_by_name = ModelMultipleChoiceFilter(
        field_name="roles__name",
        to_field_name="name",
        queryset=Role.objects.all().order_by("name"),
    )
    roles_by_pk = ModelMultipleChoiceFilter(
        field_name="roles",
        queryset=Role.objects.all().order_by("name"),
    )

    def filter_is_superuser(self, queryset, name, value):
        if value:
            return queryset.filter(groups__is_superuser=True).distinct()
        return queryset.exclude(groups__is_superuser=True).distinct()

    def filter_attributes(self, queryset, name, value):
        """Filter attributes by query args"""
        try:
            value = loads(value)
        except ValueError:
            raise ValidationError(_("filter: failed to parse JSON")) from None
        if not isinstance(value, dict):
            raise ValidationError(_("filter: value must be key:value mapping"))
        qs = {}
        for key, _value in value.items():
            qs[f"attributes__{key}"] = _value
        try:
            __ = len(queryset.filter(**qs))
            return queryset.filter(**qs)
        except ValueError:
            return queryset

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "date_joined",
            "last_updated",
            "last_login",
            "name",
            "is_active",
            "is_superuser",
            "attributes",
            "groups_by_name",
            "groups_by_pk",
            "roles_by_name",
            "roles_by_pk",
            "type",
        ]


class UserViewSet(
    ConditionalInheritance("authentik.enterprise.reports.api.reports.ExportMixin"),
    UsedByMixin,
    ModelViewSet,
):
    """User Viewset"""

    queryset = User.objects.none()
    ordering = ["username", "date_joined", "last_updated", "last_login"]
    serializer_class = UserSerializer
    filterset_class = UsersFilter
    search_fields = ["email", "name", "uuid", "username"]
    authentication_classes = [
        TokenAuthentication,
        SessionAuthentication,
        AgentAuth,
    ]

    def get_ql_fields(self):
        from djangoql.schema import BoolField, StrField

        from authentik.enterprise.search.fields import (
            ChoiceSearchField,
            JSONSearchField,
        )

        return [
            StrField(User, "username"),
            StrField(User, "name"),
            StrField(User, "email"),
            StrField(User, "path"),
            BoolField(User, "is_active", nullable=True),
            ChoiceSearchField(User, "type"),
            JSONSearchField(User, "attributes"),
        ]

    def get_queryset(self):
        base_qs = User.objects.all().exclude_anonymous()
        if self.serializer_class(context={"request": self.request})._should_include_groups:
            base_qs = base_qs.prefetch_related("groups")
        if self.serializer_class(context={"request": self.request})._should_include_roles:
            base_qs = base_qs.prefetch_related("roles")
        return base_qs

    @extend_schema(
        parameters=[
            OpenApiParameter("include_groups", bool, default=True),
            OpenApiParameter("include_roles", bool, default=True),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def _create_recovery_link(
        self, token_duration: str | None, for_email=False
    ) -> tuple[str, Token]:
        """Create a recovery link (when the current brand has a recovery flow set),
        that can either be shown to an admin or sent to the user directly"""
        brand: Brand = self.request.brand
        # Check that there is a recovery flow, if not return an error
        flow = brand.flow_recovery
        if not flow:
            raise ValidationError({"non_field_errors": _("No recovery flow set.")})
        user: User = self.get_object()
        planner = FlowPlanner(flow)
        planner.allow_empty_flows = True
        self.request._request.user = AnonymousUser()
        try:
            plan = planner.plan(
                self.request._request,
                {
                    PLAN_CONTEXT_PENDING_USER: user,
                },
            )
        except FlowNonApplicableException:
            raise ValidationError(
                {"non_field_errors": _("Recovery flow not applicable to user")}
            ) from None
        _plan = FlowToken.pickle(plan)
        if for_email:
            _plan = pickle_flow_token_for_email(plan)
        expires = default_token_duration()
        if token_duration:
            timedelta_string_validator(token_duration)
            expires = now() + timedelta_from_string(token_duration)
        token, __ = FlowToken.objects.update_or_create(
            identifier=f"{user.uid}-password-reset",
            defaults={
                "user": user,
                "flow": flow,
                "_plan": _plan,
                "revoke_on_execution": not for_email,
                "expires": expires,
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
        request=UserServiceAccountSerializer,
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
    @action(
        detail=False,
        methods=["POST"],
        pagination_class=None,
        filter_backends=[],
    )
    @validate(UserServiceAccountSerializer)
    def service_account(self, request: Request, body: UserServiceAccountSerializer) -> Response:
        """Create a new user account that is marked as a service account"""
        expires = body.validated_data.get("expires", now() + timedelta(days=360))

        username = body.validated_data["name"]
        expiring = body.validated_data["expiring"]
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
                if body.validated_data["create_group"] and self.request.user.has_perm(
                    "authentik_core.add_group"
                ):
                    group = Group.objects.create(name=username)
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
                error_msg = str(exc).lower()

                if "unique" in error_msg:
                    return Response(
                        data={
                            "non_field_errors": [
                                _("A user/group with these details already exists")
                            ]
                        },
                        status=400,
                    )
                else:
                    LOGGER.warning("Service account creation failed", exc=exc)
                    return Response(
                        data={"non_field_errors": [_("Unable to create user")]},
                        status=400,
                    )
            except (ValueError, TypeError) as exc:
                LOGGER.error("Unexpected error during service account creation", exc=exc)
                return Response(
                    data={"non_field_errors": [_("Unknown error occurred")]},
                    status=500,
                )

    @extend_schema(responses={200: SessionUserSerializer(many=False)})
    @action(
        url_path="me",
        url_name="me",
        detail=False,
        pagination_class=None,
        filter_backends=[],
    )
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
        request=UserPasswordSetSerializer,
        responses={
            204: OpenApiResponse(description="Successfully changed password"),
            400: OpenApiResponse(description="Bad request"),
        },
    )
    @action(
        detail=True,
        methods=["POST"],
        permission_classes=[IsAuthenticated],
    )
    @validate(UserPasswordSetSerializer)
    def set_password(self, request: Request, pk: int, body: UserPasswordSetSerializer) -> Response:
        """Set password for user"""
        user: User = self.get_object()
        try:
            user.set_password(body.validated_data["password"], request=request)
            user.save()
        except (ValidationError, IntegrityError) as exc:
            LOGGER.debug("Failed to set password", exc=exc)
            return Response(status=400)
        if user.pk == request.user.pk and SESSION_KEY_IMPERSONATE_USER not in self.request.session:
            LOGGER.debug("Updating session hash after password change")
            update_session_auth_hash(self.request, user)
        return Response(status=204)

    @permission_required("authentik_core.reset_user_password")
    @extend_schema(
        request=UserRecoveryLinkSerializer,
        responses={
            "200": LinkSerializer(many=False),
        },
    )
    @action(detail=True, pagination_class=None, filter_backends=[], methods=["POST"])
    @validate(UserRecoveryLinkSerializer)
    def recovery(self, request: Request, pk: int, body: UserRecoveryLinkSerializer) -> Response:
        """Create a temporary link that a user can use to recover their account"""
        link, _ = self._create_recovery_link(
            token_duration=body.validated_data.get("token_duration")
        )
        return Response({"link": link})

    @permission_required("authentik_core.reset_user_password")
    @extend_schema(
        request=UserRecoveryEmailSerializer,
        responses={
            "204": OpenApiResponse(description="Successfully sent recover email"),
        },
    )
    @action(detail=True, pagination_class=None, filter_backends=[], methods=["POST"])
    @validate(UserRecoveryEmailSerializer)
    def recovery_email(
        self, request: Request, pk: int, body: UserRecoveryEmailSerializer
    ) -> Response:
        """Send an email with a temporary link that a user can use to recover their account"""
        email_error_message = _("User does not have an email address set.")
        stage_error_message = _("Email stage not found.")
        user: User = self.get_object()
        if not user.email:
            LOGGER.debug("User doesn't have an email address")
            raise ValidationError({"non_field_errors": email_error_message})
        if not (stage := EmailStage.objects.filter(pk=body.validated_data["email_stage"]).first()):
            LOGGER.debug("Email stage does not exist")
            raise ValidationError({"non_field_errors": stage_error_message})
        if not request.user.has_perm("authentik_stages_email.view_emailstage", stage):
            LOGGER.debug("User has no view access to email stage")
            raise ValidationError({"non_field_errors": stage_error_message})
        link, token = self._create_recovery_link(
            token_duration=body.validated_data.get("token_duration"), for_email=True
        )
        message = TemplateEmailMessage(
            subject=_(stage.subject),
            to=[(user.name, user.email)],
            template_name=stage.template,
            language=user.locale(request),
            template_context={
                "url": link,
                "user": user,
                "expires": token.expires,
            },
        )
        send_mails(stage, message)
        return Response(status=204)

    @permission_required("authentik_core.impersonate")
    @extend_schema(
        request=inline_serializer(
            "ImpersonationSerializer",
            {
                "reason": CharField(required=True),
            },
        ),
        responses={
            204: OpenApiResponse(description="Successfully started impersonation"),
        },
    )
    @action(detail=True, methods=["POST"], permission_classes=[IsAuthenticated])
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
            LOGGER.debug(
                "User attempted to impersonate without permissions",
                user=request.user,
            )
            return Response(status=403)
        if user_to_be.pk == self.request.user.pk:
            LOGGER.debug("User attempted to impersonate themselves", user=request.user)
            return Response(status=401)
        if not reason and request.tenant.impersonation_require_reason:
            LOGGER.debug(
                "User attempted to impersonate without providing a reason",
                user=request.user,
            )
            raise ValidationError({"reason": _("This field is required.")})

        request.session[SESSION_KEY_IMPERSONATE_ORIGINAL_USER] = request.user
        request.session[SESSION_KEY_IMPERSONATE_USER] = user_to_be

        Event.new(EventAction.IMPERSONATION_STARTED, reason=reason).from_http(request, user_to_be)

        return Response(status=204)

    @extend_schema(
        request=None,
        responses={
            "204": OpenApiResponse(description="Successfully ended impersonation"),
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
                "UserPathSerializer",
                {"paths": ListField(child=CharField(), read_only=True)},
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
            Session.objects.filter(authenticatedsession__user=instance).delete()
            LOGGER.debug("Deleted user's sessions", user=instance.username)
        return response
