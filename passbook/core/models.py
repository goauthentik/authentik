"""passbook core models"""
from datetime import timedelta
from random import SystemRandom
from time import sleep
from typing import Any, Optional
from uuid import uuid4

from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.db import models
from django.http import HttpRequest
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django_prometheus.models import ExportModelOperationsMixin
from guardian.mixins import GuardianUserMixin
from jinja2 import Undefined
from jinja2.exceptions import TemplateSyntaxError, UndefinedError
from jinja2.nativetypes import NativeEnvironment
from model_utils.managers import InheritanceManager
from structlog import get_logger

from passbook.core.types import UIUserSettings, UILoginButton
from passbook.core.exceptions import PropertyMappingExpressionException
from passbook.core.signals import password_changed
from passbook.lib.models import CreatedUpdatedModel, UUIDModel
from passbook.policies.exceptions import PolicyException
from passbook.policies.struct import PolicyRequest, PolicyResult

LOGGER = get_logger()
NATIVE_ENVIRONMENT = NativeEnvironment()


def default_nonce_duration():
    """Default duration a Nonce is valid"""
    return now() + timedelta(hours=4)


class Group(ExportModelOperationsMixin("group"), UUIDModel):
    """Custom Group model which supports a basic hierarchy"""

    name = models.CharField(_("name"), max_length=80)
    parent = models.ForeignKey(
        "Group",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="children",
    )
    attributes = JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Group {self.name}"

    class Meta:

        unique_together = (("name", "parent",),)


class User(ExportModelOperationsMixin("user"), GuardianUserMixin, AbstractUser):
    """Custom User model to allow easier adding o f user-based settings"""

    uuid = models.UUIDField(default=uuid4, editable=False)
    name = models.TextField()

    sources = models.ManyToManyField("Source", through="UserSourceConnection")
    groups = models.ManyToManyField("Group")
    password_change_date = models.DateTimeField(auto_now_add=True)

    attributes = JSONField(default=dict, blank=True)

    def set_password(self, password):
        if self.pk:
            password_changed.send(sender=self, user=self, password=password)
        self.password_change_date = now()
        return super().set_password(password)

    class Meta:

        permissions = (("reset_user_password", "Reset Password"),)


class Provider(ExportModelOperationsMixin("provider"), models.Model):
    """Application-independent Provider instance. For example SAML2 Remote, OAuth2 Application"""

    property_mappings = models.ManyToManyField(
        "PropertyMapping", default=None, blank=True
    )

    objects = InheritanceManager()

    # This class defines no field for easier inheritance
    def __str__(self):
        if hasattr(self, "name"):
            return getattr(self, "name")
        return super().__str__()


class PolicyModel(UUIDModel, CreatedUpdatedModel):
    """Base model which can have policies applied to it"""

    policies = models.ManyToManyField("Policy", blank=True)


class Factor(ExportModelOperationsMixin("factor"), PolicyModel):
    """Authentication factor, multiple instances of the same Factor can be used"""

    name = models.TextField()
    slug = models.SlugField(unique=True)
    order = models.IntegerField()
    enabled = models.BooleanField(default=True)

    objects = InheritanceManager()
    type = ""
    form = ""

    @property
    def ui_user_settings(self) -> Optional[UIUserSettings]:
        """Entrypoint to integrate with User settings. Can either return None if no
        user settings are available, or an instanace of UIUserSettings."""
        return None

    def __str__(self):
        return f"Factor {self.slug}"


class Application(ExportModelOperationsMixin("application"), PolicyModel):
    """Every Application which uses passbook for authentication/identification/authorization
    needs an Application record. Other authentication types can subclass this Model to
    add custom fields and other properties"""

    name = models.TextField()
    slug = models.SlugField()
    skip_authorization = models.BooleanField(default=False)
    provider = models.OneToOneField(
        "Provider", null=True, blank=True, default=None, on_delete=models.SET_DEFAULT
    )

    meta_launch_url = models.URLField(null=True, blank=True)
    meta_icon_url = models.TextField(null=True, blank=True)
    meta_description = models.TextField(null=True, blank=True)
    meta_publisher = models.TextField(null=True, blank=True)

    objects = InheritanceManager()

    def get_provider(self) -> Optional[Provider]:
        """Get casted provider instance"""
        if not self.provider:
            return None
        return Provider.objects.get_subclass(pk=self.provider.pk)

    def __str__(self):
        return self.name


class Source(ExportModelOperationsMixin("source"), PolicyModel):
    """Base Authentication source, i.e. an OAuth Provider, SAML Remote or LDAP Server"""

    name = models.TextField()
    slug = models.SlugField()

    enabled = models.BooleanField(default=True)
    property_mappings = models.ManyToManyField(
        "PropertyMapping", default=None, blank=True
    )

    form = ""  # ModelForm-based class ued to create/edit instance

    objects = InheritanceManager()

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


class Policy(ExportModelOperationsMixin("policy"), UUIDModel, CreatedUpdatedModel):
    """Policies which specify if a user is authorized to use an Application. Can be overridden by
    other types to add other fields, more logic, etc."""

    name = models.TextField(blank=True, null=True)
    negate = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    timeout = models.IntegerField(default=30)

    objects = InheritanceManager()

    def __str__(self):
        return f"Policy {self.name}"

    def passes(self, request: PolicyRequest) -> PolicyResult:
        """Check if user instance passes this policy"""
        raise PolicyException()


class DebugPolicy(Policy):
    """Policy used for debugging the PolicyEngine. Returns a fixed result,
    but takes a random time to process."""

    result = models.BooleanField(default=False)
    wait_min = models.IntegerField(default=5)
    wait_max = models.IntegerField(default=30)

    form = "passbook.core.forms.policies.DebugPolicyForm"

    def passes(self, request: PolicyRequest) -> PolicyResult:
        """Wait random time then return result"""
        wait = SystemRandom().randrange(self.wait_min, self.wait_max)
        LOGGER.debug("Policy waiting", policy=self, delay=wait)
        sleep(wait)
        return PolicyResult(self.result, "Debugging")

    class Meta:

        verbose_name = _("Debug Policy")
        verbose_name_plural = _("Debug Policies")


class Invitation(ExportModelOperationsMixin("invitation"), UUIDModel):
    """Single-use invitation link"""

    created_by = models.ForeignKey("User", on_delete=models.CASCADE)
    expires = models.DateTimeField(default=None, blank=True, null=True)
    fixed_username = models.TextField(blank=True, default=None)
    fixed_email = models.TextField(blank=True, default=None)
    needs_confirmation = models.BooleanField(default=True)

    @property
    def link(self):
        """Get link to use invitation"""
        return (
            reverse_lazy("passbook_core:auth-sign-up") + f"?invitation={self.uuid.hex}"
        )

    def __str__(self):
        return f"Invitation {self.uuid.hex} created by {self.created_by}"

    class Meta:

        verbose_name = _("Invitation")
        verbose_name_plural = _("Invitations")


class Nonce(ExportModelOperationsMixin("nonce"), UUIDModel):
    """One-time link for password resets/sign-up-confirmations"""

    expires = models.DateTimeField(default=default_nonce_duration)
    user = models.ForeignKey("User", on_delete=models.CASCADE)
    expiring = models.BooleanField(default=True)
    description = models.TextField(default="", blank=True)

    @property
    def is_expired(self) -> bool:
        """Check if nonce is expired yet."""
        return now() > self.expires

    def __str__(self):
        return f"Nonce f{self.uuid.hex} {self.description} (expires={self.expires})"

    class Meta:

        verbose_name = _("Nonce")
        verbose_name_plural = _("Nonces")


class PropertyMapping(UUIDModel):
    """User-defined key -> x mapping which can be used by providers to expose extra data."""

    name = models.TextField()
    expression = models.TextField()

    form = ""
    objects = InheritanceManager()

    def evaluate(
        self, user: Optional[User], request: Optional[HttpRequest], **kwargs
    ) -> Any:
        """Evaluate `self.expression` using `**kwargs` as Context."""
        try:
            expression = NATIVE_ENVIRONMENT.from_string(self.expression)
        except TemplateSyntaxError as exc:
            raise PropertyMappingExpressionException from exc
        try:
            response = expression.render(user=user, request=request, **kwargs)
            if isinstance(response, Undefined):
                raise PropertyMappingExpressionException("Response was 'Undefined'")
            return response
        except UndefinedError as exc:
            raise PropertyMappingExpressionException from exc

    def save(self, *args, **kwargs):
        try:
            NATIVE_ENVIRONMENT.from_string(self.expression)
        except TemplateSyntaxError as exc:
            raise ValidationError("Expression Syntax Error") from exc
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"Property Mapping {self.name}"

    class Meta:

        verbose_name = _("Property Mapping")
        verbose_name_plural = _("Property Mappings")
