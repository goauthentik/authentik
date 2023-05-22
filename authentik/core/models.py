"""authentik core models"""
from datetime import timedelta
from hashlib import sha256
from typing import Any, Optional
from uuid import uuid4

from deepmerge import always_merger
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as DjangoUserManager
from django.db import models
from django.db.models import Q, QuerySet, options
from django.http import HttpRequest
from django.utils.functional import SimpleLazyObject, cached_property
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from guardian.mixins import GuardianUserMixin
from model_utils.managers import InheritanceManager
from rest_framework.serializers import Serializer
from structlog.stdlib import get_logger

from authentik.blueprints.models import ManagedModel
from authentik.core.exceptions import PropertyMappingExpressionException
from authentik.core.types import UILoginButton, UserSettingSerializer
from authentik.lib.avatars import get_avatar
from authentik.lib.config import CONFIG
from authentik.lib.generators import generate_id
from authentik.lib.models import (
    CreatedUpdatedModel,
    DomainlessFormattedURLValidator,
    SerializerModel,
)
from authentik.lib.utils.http import get_client_ip
from authentik.policies.models import PolicyBindingModel
from authentik.root.install_id import get_install_id

LOGGER = get_logger()
USER_ATTRIBUTE_DEBUG = "goauthentik.io/user/debug"
USER_ATTRIBUTE_SA = "goauthentik.io/user/service-account"
USER_ATTRIBUTE_GENERATED = "goauthentik.io/user/generated"
USER_ATTRIBUTE_EXPIRES = "goauthentik.io/user/expires"
USER_ATTRIBUTE_DELETE_ON_LOGOUT = "goauthentik.io/user/delete-on-logout"
USER_ATTRIBUTE_SOURCES = "goauthentik.io/user/sources"
USER_ATTRIBUTE_TOKEN_EXPIRING = "goauthentik.io/user/token-expires"  # nosec
USER_ATTRIBUTE_CHANGE_USERNAME = "goauthentik.io/user/can-change-username"
USER_ATTRIBUTE_CHANGE_NAME = "goauthentik.io/user/can-change-name"
USER_ATTRIBUTE_CHANGE_EMAIL = "goauthentik.io/user/can-change-email"
USER_ATTRIBUTE_CAN_OVERRIDE_IP = "goauthentik.io/user/override-ips"

USER_PATH_SYSTEM_PREFIX = "goauthentik.io"
USER_PATH_SERVICE_ACCOUNT = USER_PATH_SYSTEM_PREFIX + "/service-accounts"


options.DEFAULT_NAMES = options.DEFAULT_NAMES + ("authentik_used_by_shadows",)


def default_token_duration():
    """Default duration a Token is valid"""
    return now() + timedelta(minutes=30)


def default_token_key():
    """Default token key"""
    # We use generate_id since the chars in the key should be easy
    # to use in Emails (for verification) and URLs (for recovery)
    return generate_id(int(CONFIG.y("default_token_length")))


class Group(SerializerModel):
    """Custom Group model which supports a basic hierarchy"""

    group_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    name = models.CharField(_("name"), max_length=80)
    is_superuser = models.BooleanField(
        default=False, help_text=_("Users added to this group will be superusers.")
    )

    parent = models.ForeignKey(
        "Group",
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
        related_name="children",
    )
    attributes = models.JSONField(default=dict, blank=True)

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
        query = """
        WITH RECURSIVE parents AS (
            SELECT authentik_core_group.*, 0 AS relative_depth
            FROM authentik_core_group
            WHERE authentik_core_group.group_uuid = %s

            UNION ALL

            SELECT authentik_core_group.*, parents.relative_depth - 1
            FROM authentik_core_group,parents
            WHERE (
                authentik_core_group.parent_id = parents.group_uuid and
                parents.relative_depth > -20
            )
        )
        SELECT group_uuid
        FROM parents
        GROUP BY group_uuid;
        """
        groups = Group.objects.raw(query, [self.group_uuid])
        return user.ak_groups.filter(pk__in=[group.pk for group in groups]).exists()

    def __str__(self):
        return f"Group {self.name}"

    class Meta:
        unique_together = (
            (
                "name",
                "parent",
            ),
        )


class UserManager(DjangoUserManager):
    """Custom user manager that doesn't assign is_superuser and is_staff"""

    def create_user(self, username, email=None, password=None, **extra_fields):
        """Custom user manager that doesn't assign is_superuser and is_staff"""
        return self._create_user(username, email, password, **extra_fields)


class User(SerializerModel, GuardianUserMixin, AbstractUser):
    """Custom User model to allow easier adding of user-based settings"""

    uuid = models.UUIDField(default=uuid4, editable=False, unique=True)
    name = models.TextField(help_text=_("User's display name."))
    path = models.TextField(default="users")

    sources = models.ManyToManyField("Source", through="UserSourceConnection")
    ak_groups = models.ManyToManyField("Group", related_name="users")
    password_change_date = models.DateTimeField(auto_now_add=True)

    attributes = models.JSONField(default=dict, blank=True)

    objects = UserManager()

    @staticmethod
    def default_path() -> str:
        """Get the default user path"""
        return User._meta.get_field("path").default

    def group_attributes(self, request: Optional[HttpRequest] = None) -> dict[str, Any]:
        """Get a dictionary containing the attributes from all groups the user belongs to,
        including the users attributes"""
        final_attributes = {}
        if request and hasattr(request, "tenant"):
            always_merger.merge(final_attributes, request.tenant.attributes)
        for group in self.ak_groups.all().order_by("name"):
            always_merger.merge(final_attributes, group.attributes)
        always_merger.merge(final_attributes, self.attributes)
        return final_attributes

    @property
    def serializer(self) -> Serializer:
        from authentik.core.api.users import UserSerializer

        return UserSerializer

    @cached_property
    def is_superuser(self) -> bool:
        """Get supseruser status based on membership in a group with superuser status"""
        return self.ak_groups.filter(is_superuser=True).exists()

    @property
    def is_staff(self) -> bool:
        """superuser == staff user"""
        return self.is_superuser  # type: ignore

    def set_password(self, raw_password, signal=True):
        if self.pk and signal:
            from authentik.core.signals import password_changed

            password_changed.send(sender=self, user=self, password=raw_password)
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
        return sha256(f"{self.id}-{get_install_id()}".encode("ascii")).hexdigest()

    def locale(self, request: Optional[HttpRequest] = None) -> str:
        """Get the locale the user has configured"""
        try:
            return self.attributes.get("settings", {}).get("locale", "")
        # pylint: disable=broad-except
        except Exception as exc:
            LOGGER.warning("Failed to get default locale", exc=exc)
        if request:
            return request.tenant.locale
        return ""

    @property
    def avatar(self) -> str:
        """Get avatar, depending on authentik.avatar setting"""
        return get_avatar(self)

    class Meta:
        permissions = (
            ("reset_user_password", "Reset Password"),
            ("impersonate", "Can impersonate other users"),
        )
        verbose_name = _("User")
        verbose_name_plural = _("Users")


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
        on_delete=models.CASCADE,
        null=True,
        help_text=_("Flow used when authorizing this provider."),
        related_name="provider_authorization",
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
    def launch_url(self) -> Optional[str]:
        """URL to this provider and initiate authorization for the user.
        Can return None for providers that are not URL-based"""
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

    @property
    def serializer(self) -> Serializer:
        from authentik.core.api.applications import ApplicationSerializer

        return ApplicationSerializer

    @property
    def get_meta_icon(self) -> Optional[str]:
        """Get the URL to the App Icon image. If the name is /static or starts with http
        it is returned as-is"""
        if not self.meta_icon:
            return None
        if "://" in self.meta_icon.name or self.meta_icon.name.startswith("/static"):
            return self.meta_icon.name
        return self.meta_icon.url

    def get_launch_url(self, user: Optional["User"] = None) -> Optional[str]:
        """Get launch URL if set, otherwise attempt to get launch URL based on provider."""
        url = None
        if provider := self.get_provider():
            url = provider.launch_url
        if self.meta_launch_url:
            url = self.meta_launch_url
        if user and url:
            if isinstance(user, SimpleLazyObject):
                user._setup()
                user = user._wrapped
            try:
                return url % user.__dict__
            # pylint: disable=broad-except
            except Exception as exc:
                LOGGER.warning("Failed to format launch url", exc=exc)
                return url
        return url

    def get_provider(self) -> Optional[Provider]:
        """Get casted provider instance"""
        if not self.provider:
            return None
        # if the Application class has been cache, self.provider is set
        # but doing a direct query lookup will fail.
        # In that case, just return None
        try:
            return Provider.objects.get_subclass(pk=self.provider.pk)
        except Provider.DoesNotExist:
            return None

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = _("Application")
        verbose_name_plural = _("Applications")


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


class Source(ManagedModel, SerializerModel, PolicyBindingModel):
    """Base Authentication source, i.e. an OAuth Provider, SAML Remote or LDAP Server"""

    name = models.TextField(help_text=_("Source's display Name."))
    slug = models.SlugField(help_text=_("Internal source name, used in URLs."), unique=True)

    user_path_template = models.TextField(default="goauthentik.io/sources/%(slug)s")

    enabled = models.BooleanField(default=True)
    property_mappings = models.ManyToManyField("PropertyMapping", default=None, blank=True)
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

    objects = InheritanceManager()

    @property
    def get_icon(self) -> Optional[str]:
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
        # pylint: disable=broad-except
        except Exception as exc:
            LOGGER.warning("Failed to template user path", exc=exc, source=self)
            return User.default_path()

    @property
    def component(self) -> str:
        """Return component used to edit this object"""
        raise NotImplementedError

    def ui_login_button(self, request: HttpRequest) -> Optional[UILoginButton]:
        """If source uses a http-based flow, return UI Information about the login
        button. If source doesn't use http-based flow, return None."""
        return None

    def ui_user_settings(self) -> Optional[UserSettingSerializer]:
        """Entrypoint to integrate with User settings. Can either return None if no
        user settings are available, or UserSettingSerializer."""
        return None

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

    class Meta:
        unique_together = (("user", "source"),)


class ExpiringModel(models.Model):
    """Base Model which can expire, and is automatically cleaned up."""

    expires = models.DateTimeField(default=default_token_duration)
    expiring = models.BooleanField(default=True)

    def expire_action(self, *args, **kwargs):
        """Handler which is called when this object is expired. By
        default the object is deleted. This is less efficient compared
        to bulk deleting objects, but classes like Token() need to change
        values instead of being deleted."""
        return self.delete(*args, **kwargs)

    @classmethod
    def filter_not_expired(cls, **kwargs) -> QuerySet:
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

    class Meta:
        abstract = True


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

    def __str__(self):
        description = f"{self.identifier}"
        if self.expiring:
            description += f" (expires={self.expires})"
        return description

    class Meta:
        verbose_name = _("Token")
        verbose_name_plural = _("Tokens")
        indexes = [
            models.Index(fields=["identifier"]),
            models.Index(fields=["key"]),
        ]
        permissions = (("view_token_key", "View token's key"),)


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

    def evaluate(self, user: Optional[User], request: Optional[HttpRequest], **kwargs) -> Any:
        """Evaluate `self.expression` using `**kwargs` as Context."""
        from authentik.core.expression.evaluator import PropertyMappingEvaluator

        evaluator = PropertyMappingEvaluator(self, user, request, **kwargs)
        try:
            return evaluator.evaluate(self.expression)
        except Exception as exc:
            raise PropertyMappingExpressionException(exc) from exc

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

    @staticmethod
    def from_request(request: HttpRequest, user: User) -> Optional["AuthenticatedSession"]:
        """Create a new session from a http request"""
        if not hasattr(request, "session") or not request.session.session_key:
            return None
        return AuthenticatedSession(
            session_key=request.session.session_key,
            user=user,
            last_ip=get_client_ip(request),
            last_user_agent=request.META.get("HTTP_USER_AGENT", ""),
            expires=request.session.get_expiry_date(),
        )

    class Meta:
        verbose_name = _("Authenticated Session")
        verbose_name_plural = _("Authenticated Sessions")
