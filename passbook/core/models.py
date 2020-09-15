"""passbook core models"""
from datetime import timedelta
from typing import Any, Optional, Type
from uuid import uuid4

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as DjangoUserManager
from django.db import models
from django.db.models import Q, QuerySet
from django.forms import ModelForm
from django.http import HttpRequest
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from guardian.mixins import GuardianUserMixin
from model_utils.managers import InheritanceManager
from structlog import get_logger

from passbook.core.exceptions import PropertyMappingExpressionException
from passbook.core.signals import password_changed
from passbook.core.types import UILoginButton, UIUserSettings
from passbook.flows.models import Flow
from passbook.lib.models import CreatedUpdatedModel
from passbook.policies.models import PolicyBindingModel

LOGGER = get_logger()
PASSBOOK_USER_DEBUG = "passbook_user_debug"


def default_token_duration():
    """Default duration a Token is valid"""
    return now() + timedelta(minutes=30)


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

        unique_together = (("name", "parent",),)


class UserManager(DjangoUserManager):
    """Custom user manager that doesn't assign is_superuser and is_staff"""

    def create_user(self, username, email=None, password=None, **extra_fields):
        """Custom user manager that doesn't assign is_superuser and is_staff"""
        return self._create_user(username, email, password, **extra_fields)


class User(GuardianUserMixin, AbstractUser):
    """Custom User model to allow easier adding o f user-based settings"""

    uuid = models.UUIDField(default=uuid4, editable=False)
    name = models.TextField(help_text=_("User's display name."))

    sources = models.ManyToManyField("Source", through="UserSourceConnection")
    pb_groups = models.ManyToManyField("Group", related_name="users")
    password_change_date = models.DateTimeField(auto_now_add=True)

    attributes = models.JSONField(default=dict, blank=True)

    objects = UserManager()

    @property
    def is_superuser(self) -> bool:
        """Get supseruser status based on membership in a group with superuser status"""
        return self.pb_groups.filter(is_superuser=True).exists()

    @property
    def is_staff(self) -> bool:
        """superuser == staff user"""
        return self.is_superuser

    def set_password(self, password):
        if self.pk:
            password_changed.send(sender=self, user=self, password=password)
        self.password_change_date = now()
        return super().set_password(password)

    class Meta:

        permissions = (("reset_user_password", "Reset Password"),)
        verbose_name = _("User")
        verbose_name_plural = _("Users")


class Provider(models.Model):
    """Application-independent Provider instance. For example SAML2 Remote, OAuth2 Application"""

    authorization_flow = models.ForeignKey(
        Flow,
        on_delete=models.CASCADE,
        help_text=_("Flow used when authorizing this provider."),
        related_name="provider_authorization",
    )

    property_mappings = models.ManyToManyField(
        "PropertyMapping", default=None, blank=True
    )

    objects = InheritanceManager()

    @property
    def launch_url(self) -> Optional[str]:
        """URL to this provider and initiate authorization for the user.
        Can return None for providers that are not URL-based"""
        return None

    def form(self) -> Type[ModelForm]:
        """Return Form class used to edit this object"""
        raise NotImplementedError

    # This class defines no field for easier inheritance
    def __str__(self):
        if hasattr(self, "name"):
            return getattr(self, "name")
        return super().__str__()


class Application(PolicyBindingModel):
    """Every Application which uses passbook for authentication/identification/authorization
    needs an Application record. Other authentication types can subclass this Model to
    add custom fields and other properties"""

    name = models.TextField(help_text=_("Application's display Name."))
    slug = models.SlugField(help_text=_("Internal application name, used in URLs."))
    provider = models.OneToOneField(
        "Provider", null=True, blank=True, default=None, on_delete=models.SET_DEFAULT
    )

    meta_launch_url = models.URLField(default="", blank=True)
    meta_icon_url = models.TextField(default="", blank=True)
    meta_description = models.TextField(default="", blank=True)
    meta_publisher = models.TextField(default="", blank=True)

    def get_launch_url(self) -> Optional[str]:
        """Get launch URL if set, otherwise attempt to get launch URL based on provider."""
        if self.meta_launch_url:
            return self.meta_launch_url
        if self.provider:
            return self.provider.launch_url
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


class Source(PolicyBindingModel):
    """Base Authentication source, i.e. an OAuth Provider, SAML Remote or LDAP Server"""

    name = models.TextField(help_text=_("Source's display Name."))
    slug = models.SlugField(
        help_text=_("Internal source name, used in URLs."), unique=True
    )

    enabled = models.BooleanField(default=True)
    property_mappings = models.ManyToManyField(
        "PropertyMapping", default=None, blank=True
    )

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

    objects = InheritanceManager()

    def form(self) -> Type[ModelForm]:
        """Return Form class used to edit this object"""
        raise NotImplementedError

    @property
    def ui_login_button(self) -> Optional[UILoginButton]:
        """If source uses a http-based flow, return UI Information about the login
        button. If source doesn't use http-based flow, return None."""
        return None

    @property
    def ui_additional_info(self) -> Optional[str]:
        """Return additional Info, such as a callback URL. Show in the administration interface."""
        return None

    @property
    def ui_user_settings(self) -> Optional[UIUserSettings]:
        """Entrypoint to integrate with User settings. Can either return None if no
        user settings are available, or an instanace of UIUserSettings."""
        return None

    def __str__(self):
        return self.name


class UserSourceConnection(CreatedUpdatedModel):
    """Connection between User and Source."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    source = models.ForeignKey(Source, on_delete=models.CASCADE)

    class Meta:

        unique_together = (("user", "source"),)


class ExpiringModel(models.Model):
    """Base Model which can expire, and is automatically cleaned up."""

    expires = models.DateTimeField(default=default_token_duration)
    expiring = models.BooleanField(default=True)

    @classmethod
    def filter_not_expired(cls, **kwargs) -> QuerySet:
        """Filer for tokens which are not expired yet or are not expiring,
        and match filters in `kwargs`"""
        query = Q(**kwargs)
        query_not_expired_yet = Q(expires__lt=now(), expiring=True)
        query_not_expiring = Q(expiring=False)
        return cls.objects.filter(query & (query_not_expired_yet | query_not_expiring))

    @property
    def is_expired(self) -> bool:
        """Check if token is expired yet."""
        return now() > self.expires

    class Meta:

        abstract = True


class TokenIntents(models.TextChoices):
    """Intents a Token can be created for."""

    # Single user token
    INTENT_VERIFICATION = "verification"

    # Allow access to API
    INTENT_API = "api"


class Token(ExpiringModel):
    """Token used to authenticate the User for API Access or confirm another Stage like Email."""

    token_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    intent = models.TextField(
        choices=TokenIntents.choices, default=TokenIntents.INTENT_VERIFICATION
    )
    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="+")
    description = models.TextField(default="", blank=True)

    def __str__(self):
        return (
            f"Token {self.token_uuid.hex} {self.description} (expires={self.expires})"
        )

    class Meta:

        verbose_name = _("Token")
        verbose_name_plural = _("Tokens")


class PropertyMapping(models.Model):
    """User-defined key -> x mapping which can be used by providers to expose extra data."""

    pm_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    name = models.TextField()
    expression = models.TextField()

    objects = InheritanceManager()

    def form(self) -> Type[ModelForm]:
        """Return Form class used to edit this object"""
        raise NotImplementedError

    def evaluate(
        self, user: Optional[User], request: Optional[HttpRequest], **kwargs
    ) -> Any:
        """Evaluate `self.expression` using `**kwargs` as Context."""
        from passbook.core.expression import PropertyMappingEvaluator

        evaluator = PropertyMappingEvaluator()
        evaluator.set_context(user, request, **kwargs)
        try:
            return evaluator.evaluate(self.expression)
        except (ValueError, SyntaxError) as exc:
            raise PropertyMappingExpressionException from exc

    def __str__(self):
        return f"Property Mapping {self.name}"

    class Meta:

        verbose_name = _("Property Mapping")
        verbose_name_plural = _("Property Mappings")
