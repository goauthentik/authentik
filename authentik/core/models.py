"""authentik core models"""
from datetime import timedelta
from hashlib import md5, sha256
from typing import Any, Optional, Type
from urllib.parse import urlencode
from uuid import uuid4

from deepmerge import always_merger
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as DjangoUserManager
from django.core import validators
from django.db import models
from django.db.models import Q, QuerySet, options
from django.http import HttpRequest
from django.templatetags.static import static
from django.utils.functional import cached_property
from django.utils.html import escape
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from guardian.mixins import GuardianUserMixin
from model_utils.managers import InheritanceManager
from rest_framework.serializers import Serializer
from structlog.stdlib import get_logger

from authentik.core.exceptions import PropertyMappingExpressionException
from authentik.core.signals import password_changed
from authentik.core.types import UILoginButton, UserSettingSerializer
from authentik.flows.models import Flow
from authentik.lib.config import CONFIG
from authentik.lib.models import CreatedUpdatedModel, SerializerModel
from authentik.lib.utils.http import get_client_ip
from authentik.managed.models import ManagedModel
from authentik.policies.models import PolicyBindingModel

LOGGER = get_logger()
USER_ATTRIBUTE_DEBUG = "goauthentik.io/user/debug"
USER_ATTRIBUTE_SA = "goauthentik.io/user/service-account"
USER_ATTRIBUTE_SOURCES = "goauthentik.io/user/sources"
USER_ATTRIBUTE_TOKEN_EXPIRING = "goauthentik.io/user/token-expires"  # nosec
USER_ATTRIBUTE_CAN_OVERRIDE_IP = "goauthentik.io/user/override-ips"

GRAVATAR_URL = "https://secure.gravatar.com"
DEFAULT_AVATAR = static("dist/assets/images/user_default.png")


options.DEFAULT_NAMES = options.DEFAULT_NAMES + ("authentik_used_by_shadows",)


def default_token_duration():
    """Default duration a Token is valid"""
    return now() + timedelta(minutes=30)


def default_token_key():
    """Default token key"""
    return uuid4().hex


class Group(models.Model):
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
        on_delete=models.SET_NULL,
        related_name="children",
    )
    attributes = models.JSONField(default=dict, blank=True)

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


class User(GuardianUserMixin, AbstractUser):
    """Custom User model to allow easier adding of user-based settings"""

    uuid = models.UUIDField(default=uuid4, editable=False)
    name = models.TextField(help_text=_("User's display name."))

    sources = models.ManyToManyField("Source", through="UserSourceConnection")
    ak_groups = models.ManyToManyField("Group", related_name="users")
    password_change_date = models.DateTimeField(auto_now_add=True)

    attributes = models.JSONField(default=dict, blank=True)

    objects = UserManager()

    def group_attributes(self) -> dict[str, Any]:
        """Get a dictionary containing the attributes from all groups the user belongs to,
        including the users attributes"""
        final_attributes = {}
        for group in self.ak_groups.all().order_by("name"):
            always_merger.merge(final_attributes, group.attributes)
        always_merger.merge(final_attributes, self.attributes)
        return final_attributes

    @cached_property
    def is_superuser(self) -> bool:
        """Get supseruser status based on membership in a group with superuser status"""
        return self.ak_groups.filter(is_superuser=True).exists()

    @property
    def is_staff(self) -> bool:
        """superuser == staff user"""
        return self.is_superuser  # type: ignore

    def set_password(self, password, signal=True):
        if self.pk and signal:
            password_changed.send(sender=self, user=self, password=password)
        self.password_change_date = now()
        return super().set_password(password)

    @property
    def uid(self) -> str:
        """Generate a globall unique UID, based on the user ID and the hashed secret key"""
        return sha256(f"{self.id}-{settings.SECRET_KEY}".encode("ascii")).hexdigest()

    @property
    def avatar(self) -> str:
        """Get avatar, depending on authentik.avatar setting"""
        mode: str = CONFIG.y("avatars", "none")
        if mode == "none":
            return DEFAULT_AVATAR
        # gravatar uses md5 for their URLs, so md5 can't be avoided
        mail_hash = md5(self.email.encode("utf-8")).hexdigest()  # nosec
        if mode == "gravatar":
            parameters = [
                ("s", "158"),
                ("r", "g"),
            ]
            gravatar_url = f"{GRAVATAR_URL}/avatar/{mail_hash}?{urlencode(parameters, doseq=True)}"
            return escape(gravatar_url)
        return mode % {
            "username": self.username,
            "mail_hash": mail_hash,
            "upn": self.attributes.get("upn", ""),
        }

    class Meta:

        permissions = (
            ("reset_user_password", "Reset Password"),
            ("impersonate", "Can impersonate other users"),
        )
        verbose_name = _("User")
        verbose_name_plural = _("Users")


class Provider(SerializerModel):
    """Application-independent Provider instance. For example SAML2 Remote, OAuth2 Application"""

    name = models.TextField()

    authorization_flow = models.ForeignKey(
        Flow,
        on_delete=models.CASCADE,
        help_text=_("Flow used when authorizing this provider."),
        related_name="provider_authorization",
    )

    property_mappings = models.ManyToManyField("PropertyMapping", default=None, blank=True)

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
    def serializer(self) -> Type[Serializer]:
        """Get serializer for this model"""
        raise NotImplementedError

    def __str__(self):
        return self.name


class Application(PolicyBindingModel):
    """Every Application which uses authentik for authentication/identification/authorization
    needs an Application record. Other authentication types can subclass this Model to
    add custom fields and other properties"""

    name = models.TextField(help_text=_("Application's display Name."))
    slug = models.SlugField(help_text=_("Internal application name, used in URLs."), unique=True)
    provider = models.OneToOneField(
        "Provider", null=True, blank=True, default=None, on_delete=models.SET_DEFAULT
    )

    meta_launch_url = models.TextField(
        default="", blank=True, validators=[validators.URLValidator()]
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
    def get_meta_icon(self) -> Optional[str]:
        """Get the URL to the App Icon image. If the name is /static or starts with http
        it is returned as-is"""
        if not self.meta_icon:
            return None
        if self.meta_icon.name.startswith("http") or self.meta_icon.name.startswith("/static"):
            return self.meta_icon.name
        return self.meta_icon.url

    def get_launch_url(self) -> Optional[str]:
        """Get launch URL if set, otherwise attempt to get launch URL based on provider."""
        if self.meta_launch_url:
            return self.meta_launch_url
        if self.provider:
            return self.get_provider().launch_url
        return None

    def get_provider(self) -> Optional[Provider]:
        """Get casted provider instance"""
        if not self.provider:
            return None
        return Provider.objects.get_subclass(pk=self.provider.pk)

    def __str__(self):
        return self.name

    class Meta:

        verbose_name = _("Application")
        verbose_name_plural = _("Applications")


class SourceUserMatchingModes(models.TextChoices):
    """Different modes a source can handle new/returning users"""

    IDENTIFIER = "identifier", _("Use the source-specific identifier")
    EMAIL_LINK = "email_link", _(
        (
            "Link to a user with identical email address. Can have security implications "
            "when a source doesn't validate email addresses."
        )
    )
    EMAIL_DENY = "email_deny", _(
        "Use the user's email address, but deny enrollment when the email address already exists."
    )
    USERNAME_LINK = "username_link", _(
        (
            "Link to a user with identical username address. Can have security implications "
            "when a username is used with another source."
        )
    )
    USERNAME_DENY = "username_deny", _(
        "Use the user's username, but deny enrollment when the username already exists."
    )


class Source(ManagedModel, SerializerModel, PolicyBindingModel):
    """Base Authentication source, i.e. an OAuth Provider, SAML Remote or LDAP Server"""

    name = models.TextField(help_text=_("Source's display Name."))
    slug = models.SlugField(help_text=_("Internal source name, used in URLs."), unique=True)

    enabled = models.BooleanField(default=True)
    property_mappings = models.ManyToManyField("PropertyMapping", default=None, blank=True)

    authentication_flow = models.ForeignKey(
        Flow,
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
        help_text=_("Flow to use when authenticating existing users."),
        related_name="source_authentication",
    )
    enrollment_flow = models.ForeignKey(
        Flow,
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
            (
                "How the source determines if an existing user should be authenticated or "
                "a new user enrolled."
            )
        ),
    )

    objects = InheritanceManager()

    @property
    def component(self) -> str:
        """Return component used to edit this object"""
        raise NotImplementedError

    @property
    def ui_login_button(self) -> Optional[UILoginButton]:
        """If source uses a http-based flow, return UI Information about the login
        button. If source doesn't use http-based flow, return None."""
        return None

    @property
    def ui_user_settings(self) -> Optional[UserSettingSerializer]:
        """Entrypoint to integrate with User settings. Can either return None if no
        user settings are available, or UserSettingSerializer."""
        return None

    def __str__(self):
        return self.name


class UserSourceConnection(CreatedUpdatedModel):
    """Connection between User and Source."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    source = models.ForeignKey(Source, on_delete=models.CASCADE)

    objects = InheritanceManager()

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
        expired = Q(expires__lt=now(), expiring=True)
        return cls.objects.exclude(expired).filter(**kwargs)

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


class Token(ManagedModel, ExpiringModel):
    """Token used to authenticate the User for API Access or confirm another Stage like Email."""

    token_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    identifier = models.SlugField(max_length=255, unique=True)
    key = models.TextField(default=default_token_key)
    intent = models.TextField(
        choices=TokenIntents.choices, default=TokenIntents.INTENT_VERIFICATION
    )
    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="+")
    description = models.TextField(default="", blank=True)

    def expire_action(self, *args, **kwargs):
        """Handler which is called when this object is expired."""
        from authentik.events.models import Event, EventAction

        self.key = default_token_key()
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
    name = models.TextField()
    expression = models.TextField()

    objects = InheritanceManager()

    @property
    def component(self) -> str:
        """Return component used to edit this object"""
        raise NotImplementedError

    @property
    def serializer(self) -> Type[Serializer]:
        """Get serializer for this model"""
        raise NotImplementedError

    def evaluate(self, user: Optional[User], request: Optional[HttpRequest], **kwargs) -> Any:
        """Evaluate `self.expression` using `**kwargs` as Context."""
        from authentik.core.expression import PropertyMappingEvaluator

        evaluator = PropertyMappingEvaluator()
        evaluator.set_context(user, request, self, **kwargs)
        try:
            return evaluator.evaluate(self.expression)
        except Exception as exc:
            raise PropertyMappingExpressionException(str(exc)) from exc

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
