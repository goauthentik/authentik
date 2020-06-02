"""passbook core models"""
from datetime import timedelta
from typing import Any, Optional
from uuid import uuid4

from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.db import models
from django.http import HttpRequest
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from guardian.mixins import GuardianUserMixin
from jinja2 import Undefined
from jinja2.exceptions import TemplateSyntaxError, UndefinedError
from model_utils.managers import InheritanceManager
from structlog import get_logger

from passbook.core.exceptions import PropertyMappingExpressionException
from passbook.core.signals import password_changed
from passbook.core.types import UILoginButton, UIUserSettings
from passbook.lib.models import CreatedUpdatedModel
from passbook.policies.models import PolicyBindingModel

LOGGER = get_logger()


def default_token_duration():
    """Default duration a Token is valid"""
    return now() + timedelta(minutes=30)


class Group(models.Model):
    """Custom Group model which supports a basic hierarchy"""

    group_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)
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


class User(GuardianUserMixin, AbstractUser):
    """Custom User model to allow easier adding o f user-based settings"""

    uuid = models.UUIDField(default=uuid4, editable=False)
    name = models.TextField(help_text=_("User's display name."))

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


class Provider(models.Model):
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


class Application(PolicyBindingModel):
    """Every Application which uses passbook for authentication/identification/authorization
    needs an Application record. Other authentication types can subclass this Model to
    add custom fields and other properties"""

    name = models.TextField(help_text=_("Application's display Name."))
    slug = models.SlugField(help_text=_("Internal application name, used in URLs."))
    skip_authorization = models.BooleanField(default=False)
    provider = models.OneToOneField(
        "Provider", null=True, blank=True, default=None, on_delete=models.SET_DEFAULT
    )

    meta_launch_url = models.URLField(default="", blank=True)
    meta_icon_url = models.TextField(default="", blank=True)
    meta_description = models.TextField(default="", blank=True)
    meta_publisher = models.TextField(default="", blank=True)

    objects = InheritanceManager()

    def get_provider(self) -> Optional[Provider]:
        """Get casted provider instance"""
        if not self.provider:
            return None
        return Provider.objects.get_subclass(pk=self.provider.pk)

    def __str__(self):
        return self.name


class Source(PolicyBindingModel):
    """Base Authentication source, i.e. an OAuth Provider, SAML Remote or LDAP Server"""

    name = models.TextField(help_text=_("Source's display Name."))
    slug = models.SlugField(help_text=_("Internal source name, used in URLs."))

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


class Token(models.Model):
    """One-time link for password resets/sign-up-confirmations"""

    token_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    expires = models.DateTimeField(default=default_token_duration)
    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="+")
    expiring = models.BooleanField(default=True)
    description = models.TextField(default="", blank=True)

    @property
    def is_expired(self) -> bool:
        """Check if token is expired yet."""
        return now() > self.expires

    def __str__(self):
        return (
            f"Token f{self.token_uuid.hex} {self.description} (expires={self.expires})"
        )

    class Meta:

        verbose_name = _("Token")
        verbose_name_plural = _("Tokens")


class PropertyMapping(models.Model):
    """User-defined key -> x mapping which can be used by providers to expose extra data."""

    pm_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    name = models.TextField()
    expression = models.TextField()

    form = ""
    objects = InheritanceManager()

    def evaluate(
        self, user: Optional[User], request: Optional[HttpRequest], **kwargs
    ) -> Any:
        """Evaluate `self.expression` using `**kwargs` as Context."""
        from passbook.policies.expression.evaluator import Evaluator

        evaluator = Evaluator()
        try:
            expression = evaluator.env.from_string(self.expression)
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
        from passbook.policies.expression.evaluator import Evaluator

        evaluator = Evaluator()
        try:
            evaluator.env.from_string(self.expression)
        except TemplateSyntaxError as exc:
            raise ValidationError("Expression Syntax Error") from exc
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"Property Mapping {self.name}"

    class Meta:

        verbose_name = _("Property Mapping")
        verbose_name_plural = _("Property Mappings")
