"""authentik core models"""

from datetime import datetime
from hashlib import sha256
from typing import Any, Optional, Self
from uuid import uuid4

from deepmerge import always_merger
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as DjangoUserManager
from django.db import models
from django.db.models import Q, QuerySet, options
from django.db.models.constants import LOOKUP_SEP
from django.http import HttpRequest
from django.utils.functional import SimpleLazyObject, cached_property
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django_cte import CTEQuerySet, With
from guardian.conf import settings
from guardian.mixins import GuardianUserMixin
from model_utils.managers import InheritanceManager
from rest_framework.serializers import Serializer
from structlog.stdlib import get_logger

from authentik.blueprints.models import ManagedModel
from authentik.core.expression.exceptions import PropertyMappingExpressionException
from authentik.core.types import UILoginButton, UserSettingSerializer
from authentik.lib.avatars import get_avatar
from authentik.lib.expression.exceptions import ControlFlowException
from authentik.lib.generators import generate_id
from authentik.lib.merge import MERGE_LIST_UNIQUE
from authentik.lib.models import (
    CreatedUpdatedModel,
    DomainlessFormattedURLValidator,
    SerializerModel,
)
from authentik.lib.utils.time import timedelta_from_string
from authentik.policies.models import PolicyBindingModel
from authentik.tenants.models import DEFAULT_TOKEN_DURATION, DEFAULT_TOKEN_LENGTH
from authentik.tenants.utils import get_current_tenant, get_unique_identifier

LOGGER = get_logger()
USER_ATTRIBUTE_DEBUG = "goauthentik.io/user/debug"
USER_ATTRIBUTE_GENERATED = "goauthentik.io/user/generated"
USER_ATTRIBUTE_EXPIRES = "goauthentik.io/user/expires"
USER_ATTRIBUTE_DELETE_ON_LOGOUT = "goauthentik.io/user/delete-on-logout"
USER_ATTRIBUTE_SOURCES = "goauthentik.io/user/sources"
USER_ATTRIBUTE_TOKEN_EXPIRING = "goauthentik.io/user/token-expires"  # nosec
USER_ATTRIBUTE_TOKEN_MAXIMUM_LIFETIME = "goauthentik.io/user/token-maximum-lifetime"  # nosec
USER_ATTRIBUTE_CHANGE_USERNAME = "goauthentik.io/user/can-change-username"
USER_ATTRIBUTE_CHANGE_NAME = "goauthentik.io/user/can-change-name"
USER_ATTRIBUTE_CHANGE_EMAIL = "goauthentik.io/user/can-change-email"
USER_PATH_SYSTEM_PREFIX = "goauthentik.io"
USER_PATH_SERVICE_ACCOUNT = USER_PATH_SYSTEM_PREFIX + "/service-accounts"

options.DEFAULT_NAMES = options.DEFAULT_NAMES + (
    # used_by API that allows models to specify if they shadow an object
    # for example the proxy provider which is built on top of an oauth provider
    "authentik_used_by_shadows",
)

GROUP_RECURSION_LIMIT = 20


def default_token_duration() -> datetime:
    """Default duration a Token is valid"""
    current_tenant = get_current_tenant()
    token_duration = (
        current_tenant.default_token_duration
        if hasattr(current_tenant, "default_token_duration")
        else DEFAULT_TOKEN_DURATION
    )
    return now() + timedelta_from_string(token_duration)


def default_token_key() -> str:
    """Default token key"""
    current_tenant = get_current_tenant()
    token_length = (
        current_tenant.default_token_length
        if hasattr(current_tenant, "default_token_length")
        else DEFAULT_TOKEN_LENGTH
    )
    # We use generate_id since the chars in the key should be easy
    # to use in Emails (for verification) and URLs (for recovery)
    return generate_id(token_length)


class UserTypes(models.TextChoices):
    """User types, both for grouping, licensing and permissions in the case
    of the internal_service_account"""

    INTERNAL = "internal"
    EXTERNAL = "external"

    # User-created service accounts
    SERVICE_ACCOUNT = "service_account"

    # Special user type for internally managed and created service
    # accounts, such as outpost users
    INTERNAL_SERVICE_ACCOUNT = "internal_service_account"


class AttributesMixin(models.Model):
    """Adds an attributes property to a model"""

    attributes = models.JSONField(default=dict, blank=True)

    class Meta:
        abstract = True

    def update_attributes(self, properties: dict[str, Any]):
        """Update fields and attributes, but correctly by merging dicts"""
        for key, value in properties.items():
            if key == "attributes":
                continue
            setattr(self, key, value)
        final_attributes = {}
        MERGE_LIST_UNIQUE.merge(final_attributes, self.attributes)
        MERGE_LIST_UNIQUE.merge(final_attributes, properties.get("attributes", {}))
        self.attributes = final_attributes
        self.save()

    @classmethod
    def update_or_create_attributes(
        cls, query: dict[str, Any], properties: dict[str, Any]
    ) -> tuple[models.Model, bool]:
        """Same as django's update_or_create but correctly updates attributes by merging dicts"""
        instance = cls.objects.filter(**query).first()
        if not instance:
            return cls.objects.create(**properties), True
        instance.update_attributes(properties)
        return instance, False


class GroupQuerySet(CTEQuerySet):
    def with_children_recursive(self):
        """Recursively get all groups that have the current queryset as parents
        or are indirectly related."""

        def make_cte(cte):
            """Build the query that ends up in WITH RECURSIVE"""
            # Start from self, aka the current query
            # Add a depth attribute to limit the recursion
            return self.annotate(
                relative_depth=models.Value(0, output_field=models.IntegerField())
            ).union(
                # Here is the recursive part of the query. cte refers to the previous iteration
                # Only select groups for which the parent is part of the previous iteration
                # and increase the depth
                # Finally, limit the depth
                cte.join(Group, group_uuid=cte.col.parent_id)
                .annotate(
                    relative_depth=models.ExpressionWrapper(
                        cte.col.relative_depth
                        + models.Value(1, output_field=models.IntegerField()),
                        output_field=models.IntegerField(),
                    )
                )
                .filter(relative_depth__lt=GROUP_RECURSION_LIMIT),
                all=True,
            )

        # Build the recursive query, see above
        cte = With.recursive(make_cte)
        # Return the result, as a usable queryset for Group.
        return cte.join(Group, group_uuid=cte.col.group_uuid).with_cte(cte)


class Group(SerializerModel, AttributesMixin):
    """Group model which supports a basic hierarchy and has attributes"""

    group_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    name = models.TextField(_("name"))
    is_superuser = models.BooleanField(
        default=False, help_text=_("Users added to this group will be superusers.")
    )

    roles = models.ManyToManyField("authentik_rbac.Role", related_name="ak_groups", blank=True)

    parent = models.ForeignKey(
        "Group",
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
        related_name="children",
    )

    objects = GroupQuerySet.as_manager()

    class Meta:
        unique_together = (
            (
                "name",
                "parent",
            ),
        )
        indexes = [models.Index(fields=["name"])]
        verbose_name = _("Group")
        verbose_name_plural = _("Groups")
        permissions = [
            ("add_user_to_group", _("Add user to group")),
            ("remove_user_from_group", _("Remove user from group")),
        ]

    def __str__(self):
        return f"Group {self.name}"

    @property
    def serializer(self) -> Serializer:
        from authentik.core.api.groups import GroupSerializer

        return GroupSerializer

    @property
    def num_pk(self) -> int:
        """Get a numerical, int32 ID for the group"""
        # int max is 2147483647 (10 digits) so 9 is the max usable
        # in the LDAP Outpost we use the last 5 chars so match here
        return int(str(self.pk.int)[:5])

    def is_member(self, user: "User") -> bool:
        """Recursively check if `user` is member of us, or any parent."""
        return user.all_groups().filter(group_uuid=self.group_uuid).exists()

    def children_recursive(self: Self | QuerySet["Group"]) -> QuerySet["Group"]:
        """Compatibility layer for Group.objects.with_children_recursive()"""
        qs = self
        if not isinstance(self, QuerySet):
            qs = Group.objects.filter(group_uuid=self.group_uuid)
        return qs.with_children_recursive()


class UserQuerySet(models.QuerySet):
    """User queryset"""

    def exclude_anonymous(self):
        """Exclude anonymous user"""
        return self.exclude(**{User.USERNAME_FIELD: settings.ANONYMOUS_USER_NAME})


class UserManager(DjangoUserManager):
    """User manager that doesn't assign is_superuser and is_staff"""

    def get_queryset(self):
        """Create special user queryset"""
        return UserQuerySet(self.model, using=self._db)

    def create_user(self, username, email=None, password=None, **extra_fields):
        """User manager that doesn't assign is_superuser and is_staff"""
        return self._create_user(username, email, password, **extra_fields)

    def exclude_anonymous(self) -> QuerySet:
        """Exclude anonymous user"""
        return self.get_queryset().exclude_anonymous()


class User(SerializerModel, GuardianUserMixin, AttributesMixin, AbstractUser):
    """authentik User model, based on django's contrib auth user model."""

    uuid = models.UUIDField(default=uuid4, editable=False, unique=True)
    name = models.TextField(help_text=_("User's display name."))
    path = models.TextField(default="users")
    type = models.TextField(choices=UserTypes.choices, default=UserTypes.INTERNAL)

    sources = models.ManyToManyField("Source", through="UserSourceConnection")
    ak_groups = models.ManyToManyField("Group", related_name="users")
    password_change_date = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        permissions = [
            ("reset_user_password", _("Reset Password")),
            ("impersonate", _("Can impersonate other users")),
            ("assign_user_permissions", _("Can assign permissions to users")),
            ("unassign_user_permissions", _("Can unassign permissions from users")),
            ("preview_user", _("Can preview user data sent to providers")),
            ("view_user_applications", _("View applications the user has access to")),
        ]
        indexes = [
            models.Index(fields=["last_login"]),
            models.Index(fields=["password_change_date"]),
            models.Index(fields=["uuid"]),
            models.Index(fields=["path"]),
            models.Index(fields=["type"]),
        ]

    def __str__(self):
        return self.username

    @staticmethod
    def default_path() -> str:
        """Get the default user path"""
        return User._meta.get_field("path").default

    def all_groups(self) -> QuerySet[Group]:
        """Recursively get all groups this user is a member of."""
        return self.ak_groups.all().with_children_recursive()

    def group_attributes(self, request: HttpRequest | None = None) -> dict[str, Any]:
        """Get a dictionary containing the attributes from all groups the user belongs to,
        including the users attributes"""
        final_attributes = {}
        if request and hasattr(request, "brand"):
            always_merger.merge(final_attributes, request.brand.attributes)
        for group in self.all_groups().order_by("name"):
            always_merger.merge(final_attributes, group.attributes)
        always_merger.merge(final_attributes, self.attributes)
        return final_attributes

    def app_entitlements(self, app: "Application | None") -> QuerySet["ApplicationEntitlement"]:
        """Get all entitlements this user has for `app`."""
        if not app:
            return []
        all_groups = self.all_groups()
        qs = app.applicationentitlement_set.filter(
            Q(
                Q(bindings__user=self) | Q(bindings__group__in=all_groups),
                bindings__negate=False,
            )
            | Q(
                Q(~Q(bindings__user=self), bindings__user__isnull=False)
                | Q(~Q(bindings__group__in=all_groups), bindings__group__isnull=False),
                bindings__negate=True,
            ),
            bindings__enabled=True,
        ).order_by("name")
        return qs

    def app_entitlements_attributes(self, app: "Application | None") -> dict:
        """Get a dictionary containing all merged attributes from app entitlements for `app`."""
        final_attributes = {}
        for attrs in self.app_entitlements(app).values_list("attributes", flat=True):
            always_merger.merge(final_attributes, attrs)
        return final_attributes

    @property
    def serializer(self) -> Serializer:
        from authentik.core.api.users import UserSerializer

        return UserSerializer

    @cached_property
    def is_superuser(self) -> bool:
        """Get supseruser status based on membership in a group with superuser status"""
        return self.all_groups().filter(is_superuser=True).exists()

    @property
    def is_staff(self) -> bool:
        """superuser == staff user"""
        return self.is_superuser  # type: ignore

    def set_password(self, raw_password, signal=True, sender=None, request=None):
        if self.pk and signal:
            from authentik.core.signals import password_changed

            if not sender:
                sender = self
            password_changed.send(sender=sender, user=self, password=raw_password, request=request)
        self.password_change_date = now()
        return super().set_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        """
        Return a boolean of whether the raw_password was correct. Handles
        hashing formats behind the scenes.

        Slightly changed version which doesn't send a signal for such internal hash upgrades
        """

        def setter(raw_password):
            self.set_password(raw_password, signal=False)
            # Password hash upgrades shouldn't be considered password changes.
            self._password = None
            self.save(update_fields=["password"])

        return check_password(raw_password, self.password, setter)

    @property
    def uid(self) -> str:
        """Generate a globally unique UID, based on the user ID and the hashed secret key"""
        return sha256(f"{self.id}-{get_unique_identifier()}".encode("ascii")).hexdigest()

    def locale(self, request: HttpRequest | None = None) -> str:
        """Get the locale the user has configured"""
        try:
            return self.attributes.get("settings", {}).get("locale", "")

        except Exception as exc:
            LOGGER.warning("Failed to get default locale", exc=exc)
        if request:
            return request.brand.locale
        return ""

    @property
    def avatar(self) -> str:
        """Get avatar, depending on authentik.avatar setting"""
        return get_avatar(self)


class Provider(SerializerModel):
    """Application-independent Provider instance. For example SAML2 Remote, OAuth2 Application"""

    name = models.TextField(unique=True)

    authentication_flow = models.ForeignKey(
        "authentik_flows.Flow",
        null=True,
        on_delete=models.SET_NULL,
        help_text=_(
            "Flow used for authentication when the associated application is accessed by an "
            "un-authenticated user."
        ),
        related_name="provider_authentication",
    )
    authorization_flow = models.ForeignKey(
        "authentik_flows.Flow",
        # Set to cascade even though null is allowed, since most providers
        # still require an authorization flow set
        on_delete=models.CASCADE,
        null=True,
        help_text=_("Flow used when authorizing this provider."),
        related_name="provider_authorization",
    )
    invalidation_flow = models.ForeignKey(
        "authentik_flows.Flow",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        help_text=_("Flow used ending the session from a provider."),
        related_name="provider_invalidation",
    )

    property_mappings = models.ManyToManyField("PropertyMapping", default=None, blank=True)

    backchannel_application = models.ForeignKey(
        "Application",
        default=None,
        null=True,
        on_delete=models.CASCADE,
        help_text=_(
            "Accessed from applications; optional backchannel providers for protocols "
            "like LDAP and SCIM."
        ),
        related_name="backchannel_providers",
    )

    is_backchannel = models.BooleanField(default=False)

    objects = InheritanceManager()

    @property
    def launch_url(self) -> str | None:
        """URL to this provider and initiate authorization for the user.
        Can return None for providers that are not URL-based"""
        return None

    @property
    def icon_url(self) -> str | None:
        return None

    @property
    def component(self) -> str:
        """Return component used to edit this object"""
        raise NotImplementedError

    @property
    def serializer(self) -> type[Serializer]:
        """Get serializer for this model"""
        raise NotImplementedError

    def __str__(self):
        return str(self.name)


class BackchannelProvider(Provider):
    """Base class for providers that augment other providers, for example LDAP and SCIM.
    Multiple of these providers can be configured per application, they may not use the application
    slug in URLs as an application may have multiple instances of the same
    type of Backchannel provider

    They can use the application's policies and metadata"""

    @property
    def component(self) -> str:
        raise NotImplementedError

    @property
    def serializer(self) -> type[Serializer]:
        raise NotImplementedError

    class Meta:
        abstract = True


class ApplicationQuerySet(QuerySet):
    def with_provider(self) -> "QuerySet[Application]":
        qs = self.select_related("provider")
        for subclass in Provider.objects.get_queryset()._get_subclasses_recurse(Provider):
            qs = qs.select_related(f"provider__{subclass}")
        return qs


class Application(SerializerModel, PolicyBindingModel):
    """Every Application which uses authentik for authentication/identification/authorization
    needs an Application record. Other authentication types can subclass this Model to
    add custom fields and other properties"""

    name = models.TextField(help_text=_("Application's display Name."))
    slug = models.SlugField(help_text=_("Internal application name, used in URLs."), unique=True)
    group = models.TextField(blank=True, default="")

    provider = models.OneToOneField(
        "Provider", null=True, blank=True, default=None, on_delete=models.SET_DEFAULT
    )

    meta_launch_url = models.TextField(
        default="", blank=True, validators=[DomainlessFormattedURLValidator()]
    )

    open_in_new_tab = models.BooleanField(
        default=False, help_text=_("Open launch URL in a new browser tab or window.")
    )

    # For template applications, this can be set to /static/authentik/applications/*
    meta_icon = models.FileField(
        upload_to="application-icons/",
        default=None,
        null=True,
        max_length=500,
    )
    meta_description = models.TextField(default="", blank=True)
    meta_publisher = models.TextField(default="", blank=True)

    objects = ApplicationQuerySet.as_manager()

    @property
    def serializer(self) -> Serializer:
        from authentik.core.api.applications import ApplicationSerializer

        return ApplicationSerializer

    @property
    def get_meta_icon(self) -> str | None:
        """Get the URL to the App Icon image. If the name is /static or starts with http
        it is returned as-is"""
        if not self.meta_icon:
            return None
        if "://" in self.meta_icon.name or self.meta_icon.name.startswith("/static"):
            return self.meta_icon.name
        return self.meta_icon.url

    def get_launch_url(self, user: Optional["User"] = None) -> str | None:
        """Get launch URL if set, otherwise attempt to get launch URL based on provider."""
        url = None
        if self.meta_launch_url:
            url = self.meta_launch_url
        elif provider := self.get_provider():
            url = provider.launch_url
        if user and url:
            if isinstance(user, SimpleLazyObject):
                user._setup()
                user = user._wrapped
            try:
                return url % user.__dict__

            except Exception as exc:
                LOGGER.warning("Failed to format launch url", exc=exc)
                return url
        return url

    def get_provider(self) -> Provider | None:
        """Get casted provider instance. Needs Application queryset with_provider"""
        if not self.provider:
            return None

        candidates = []
        base_class = Provider
        for subclass in base_class.objects.get_queryset()._get_subclasses_recurse(base_class):
            parent = self.provider
            for level in subclass.split(LOOKUP_SEP):
                try:
                    parent = getattr(parent, level)
                except AttributeError:
                    break
            if parent in candidates:
                continue
            idx = subclass.count(LOOKUP_SEP)
            if type(parent) is not base_class:
                idx += 1
            candidates.insert(idx, parent)
        if not candidates:
            return None
        return candidates[-1]

    def backchannel_provider_for[T: Provider](self, provider_type: type[T], **kwargs) -> T | None:
        """Get Backchannel provider for a specific type"""
        providers = self.backchannel_providers.filter(
            **{f"{provider_type._meta.model_name}__isnull": False},
            **kwargs,
        )
        return getattr(providers.first(), provider_type._meta.model_name)

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = _("Application")
        verbose_name_plural = _("Applications")


class ApplicationEntitlement(AttributesMixin, SerializerModel, PolicyBindingModel):
    """Application-scoped entitlement to control authorization in an application"""

    name = models.TextField()

    app = models.ForeignKey(Application, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("Application Entitlement")
        verbose_name_plural = _("Application Entitlements")
        unique_together = (("app", "name"),)

    def __str__(self):
        return f"Application Entitlement {self.name} for app {self.app_id}"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.core.api.application_entitlements import ApplicationEntitlementSerializer

        return ApplicationEntitlementSerializer

    def supported_policy_binding_targets(self):
        return ["group", "user"]


class SourceUserMatchingModes(models.TextChoices):
    """Different modes a source can handle new/returning users"""

    IDENTIFIER = "identifier", _("Use the source-specific identifier")
    EMAIL_LINK = "email_link", _(
        "Link to a user with identical email address. Can have security implications "
        "when a source doesn't validate email addresses."
    )
    EMAIL_DENY = "email_deny", _(
        "Use the user's email address, but deny enrollment when the email address already exists."
    )
    USERNAME_LINK = "username_link", _(
        "Link to a user with identical username. Can have security implications "
        "when a username is used with another source."
    )
    USERNAME_DENY = "username_deny", _(
        "Use the user's username, but deny enrollment when the username already exists."
    )


class SourceGroupMatchingModes(models.TextChoices):
    """Different modes a source can handle new/returning groups"""

    IDENTIFIER = "identifier", _("Use the source-specific identifier")
    NAME_LINK = "name_link", _(
        "Link to a group with identical name. Can have security implications "
        "when a group name is used with another source."
    )
    NAME_DENY = "name_deny", _(
        "Use the group name, but deny enrollment when the name already exists."
    )


class Source(ManagedModel, SerializerModel, PolicyBindingModel):
    """Base Authentication source, i.e. an OAuth Provider, SAML Remote or LDAP Server"""

    name = models.TextField(help_text=_("Source's display Name."))
    slug = models.SlugField(help_text=_("Internal source name, used in URLs."), unique=True)

    user_path_template = models.TextField(default="goauthentik.io/sources/%(slug)s")

    enabled = models.BooleanField(default=True)
    user_property_mappings = models.ManyToManyField(
        "PropertyMapping", default=None, blank=True, related_name="source_userpropertymappings_set"
    )
    group_property_mappings = models.ManyToManyField(
        "PropertyMapping", default=None, blank=True, related_name="source_grouppropertymappings_set"
    )
    icon = models.FileField(
        upload_to="source-icons/",
        default=None,
        null=True,
        max_length=500,
    )

    authentication_flow = models.ForeignKey(
        "authentik_flows.Flow",
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
        help_text=_("Flow to use when authenticating existing users."),
        related_name="source_authentication",
    )
    enrollment_flow = models.ForeignKey(
        "authentik_flows.Flow",
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
        help_text=_("Flow to use when enrolling new users."),
        related_name="source_enrollment",
    )

    user_matching_mode = models.TextField(
        choices=SourceUserMatchingModes.choices,
        default=SourceUserMatchingModes.IDENTIFIER,
        help_text=_(
            "How the source determines if an existing user should be authenticated or "
            "a new user enrolled."
        ),
    )
    group_matching_mode = models.TextField(
        choices=SourceGroupMatchingModes.choices,
        default=SourceGroupMatchingModes.IDENTIFIER,
        help_text=_(
            "How the source determines if an existing group should be used or "
            "a new group created."
        ),
    )

    objects = InheritanceManager()

    @property
    def icon_url(self) -> str | None:
        """Get the URL to the Icon. If the name is /static or
        starts with http it is returned as-is"""
        if not self.icon:
            return None
        if "://" in self.icon.name or self.icon.name.startswith("/static"):
            return self.icon.name
        return self.icon.url

    def get_user_path(self) -> str:
        """Get user path, fallback to default for formatting errors"""
        try:
            return self.user_path_template % {
                "slug": self.slug,
            }

        except Exception as exc:
            LOGGER.warning("Failed to template user path", exc=exc, source=self)
            return User.default_path()

    @property
    def component(self) -> str:
        """Return component used to edit this object"""
        raise NotImplementedError

    @property
    def property_mapping_type(self) -> "type[PropertyMapping]":
        """Return property mapping type used by this object"""
        raise NotImplementedError

    def ui_login_button(self, request: HttpRequest) -> UILoginButton | None:
        """If source uses a http-based flow, return UI Information about the login
        button. If source doesn't use http-based flow, return None."""
        return None

    def ui_user_settings(self) -> UserSettingSerializer | None:
        """Entrypoint to integrate with User settings. Can either return None if no
        user settings are available, or UserSettingSerializer."""
        return None

    def get_base_user_properties(self, **kwargs) -> dict[str, Any | dict[str, Any]]:
        """Get base properties for a user to build final properties upon."""
        raise NotImplementedError

    def get_base_group_properties(self, **kwargs) -> dict[str, Any | dict[str, Any]]:
        """Get base properties for a group to build final properties upon."""
        raise NotImplementedError

    def __str__(self):
        return str(self.name)

    class Meta:
        indexes = [
            models.Index(
                fields=[
                    "slug",
                ]
            ),
            models.Index(
                fields=[
                    "name",
                ]
            ),
            models.Index(
                fields=[
                    "enabled",
                ]
            ),
        ]


class UserSourceConnection(SerializerModel, CreatedUpdatedModel):
    """Connection between User and Source."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    source = models.ForeignKey(Source, on_delete=models.CASCADE)

    objects = InheritanceManager()

    @property
    def serializer(self) -> type[Serializer]:
        """Get serializer for this model"""
        raise NotImplementedError

    def __str__(self) -> str:
        return f"User-source connection (user={self.user_id}, source={self.source_id})"

    class Meta:
        unique_together = (("user", "source"),)


class GroupSourceConnection(SerializerModel, CreatedUpdatedModel):
    """Connection between Group and Source."""

    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    source = models.ForeignKey(Source, on_delete=models.CASCADE)
    identifier = models.TextField()

    objects = InheritanceManager()

    @property
    def serializer(self) -> type[Serializer]:
        """Get serializer for this model"""
        raise NotImplementedError

    def __str__(self) -> str:
        return f"Group-source connection (group={self.group_id}, source={self.source_id})"

    class Meta:
        unique_together = (("group", "source"),)


class ExpiringModel(models.Model):
    """Base Model which can expire, and is automatically cleaned up."""

    expires = models.DateTimeField(default=None, null=True)
    expiring = models.BooleanField(default=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["expires"]),
            models.Index(fields=["expiring"]),
            models.Index(fields=["expiring", "expires"]),
        ]

    def expire_action(self, *args, **kwargs):
        """Handler which is called when this object is expired. By
        default the object is deleted. This is less efficient compared
        to bulk deleting objects, but classes like Token() need to change
        values instead of being deleted."""
        return self.delete(*args, **kwargs)

    @classmethod
    def filter_not_expired(cls, **kwargs) -> QuerySet["Token"]:
        """Filer for tokens which are not expired yet or are not expiring,
        and match filters in `kwargs`"""
        for obj in cls.objects.filter(**kwargs).filter(Q(expires__lt=now(), expiring=True)):
            obj.delete()
        return cls.objects.filter(**kwargs)

    @property
    def is_expired(self) -> bool:
        """Check if token is expired yet."""
        if not self.expiring:
            return False
        return now() > self.expires


class TokenIntents(models.TextChoices):
    """Intents a Token can be created for."""

    # Single use token
    INTENT_VERIFICATION = "verification"

    # Allow access to API
    INTENT_API = "api"

    # Recovery use for the recovery app
    INTENT_RECOVERY = "recovery"

    # App-specific passwords
    INTENT_APP_PASSWORD = "app_password"  # nosec


class Token(SerializerModel, ManagedModel, ExpiringModel):
    """Token used to authenticate the User for API Access or confirm another Stage like Email."""

    token_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    identifier = models.SlugField(max_length=255, unique=True)
    key = models.TextField(default=default_token_key)
    intent = models.TextField(
        choices=TokenIntents.choices, default=TokenIntents.INTENT_VERIFICATION
    )
    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="+")
    description = models.TextField(default="", blank=True)

    class Meta:
        verbose_name = _("Token")
        verbose_name_plural = _("Tokens")
        indexes = ExpiringModel.Meta.indexes + [
            models.Index(fields=["identifier"]),
            models.Index(fields=["key"]),
        ]
        permissions = [("view_token_key", _("View token's key"))]

    def __str__(self):
        description = f"{self.identifier}"
        if self.expiring:
            description += f" (expires={self.expires})"
        return description

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.core.api.tokens import TokenSerializer

        return TokenSerializer

    def expire_action(self, *args, **kwargs):
        """Handler which is called when this object is expired."""
        from authentik.events.models import Event, EventAction

        if self.intent in [
            TokenIntents.INTENT_RECOVERY,
            TokenIntents.INTENT_VERIFICATION,
            TokenIntents.INTENT_APP_PASSWORD,
        ]:
            super().expire_action(*args, **kwargs)
            return

        self.key = default_token_key()
        self.expires = default_token_duration()
        self.save(*args, **kwargs)
        Event.new(
            action=EventAction.SECRET_ROTATE,
            token=self,
            message=f"Token {self.identifier}'s secret was rotated.",
        ).save()


class PropertyMapping(SerializerModel, ManagedModel):
    """User-defined key -> x mapping which can be used by providers to expose extra data."""

    pm_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    name = models.TextField(unique=True)
    expression = models.TextField()

    objects = InheritanceManager()

    @property
    def component(self) -> str:
        """Return component used to edit this object"""
        raise NotImplementedError

    @property
    def serializer(self) -> type[Serializer]:
        """Get serializer for this model"""
        raise NotImplementedError

    def evaluate(self, user: User | None, request: HttpRequest | None, **kwargs) -> Any:
        """Evaluate `self.expression` using `**kwargs` as Context."""
        from authentik.core.expression.evaluator import PropertyMappingEvaluator

        evaluator = PropertyMappingEvaluator(self, user, request, **kwargs)
        try:
            return evaluator.evaluate(self.expression)
        except ControlFlowException as exc:
            raise exc
        except Exception as exc:
            raise PropertyMappingExpressionException(exc, self) from exc

    def __str__(self):
        return f"Property Mapping {self.name}"

    class Meta:
        verbose_name = _("Property Mapping")
        verbose_name_plural = _("Property Mappings")


class AuthenticatedSession(ExpiringModel):
    """Additional session class for authenticated users. Augments the standard django session
    to achieve the following:
        - Make it queryable by user
        - Have a direct connection to user objects
        - Allow users to view their own sessions and terminate them
        - Save structured and well-defined information.
    """

    uuid = models.UUIDField(default=uuid4, primary_key=True)

    session_key = models.CharField(max_length=40)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    last_ip = models.TextField()
    last_user_agent = models.TextField(blank=True)
    last_used = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Authenticated Session")
        verbose_name_plural = _("Authenticated Sessions")
        indexes = ExpiringModel.Meta.indexes + [
            models.Index(fields=["session_key"]),
        ]

    def __str__(self) -> str:
        return f"Authenticated Session {self.session_key[:10]}"

    @staticmethod
    def from_request(request: HttpRequest, user: User) -> Optional["AuthenticatedSession"]:
        """Create a new session from a http request"""
        from authentik.root.middleware import ClientIPMiddleware

        if not hasattr(request, "session") or not request.session.session_key:
            return None
        return AuthenticatedSession(
            session_key=request.session.session_key,
            user=user,
            last_ip=ClientIPMiddleware.get_client_ip(request),
            last_user_agent=request.META.get("HTTP_USER_AGENT", ""),
            expires=request.session.get_expiry_date(),
        )
