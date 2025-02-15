from django.contrib.auth import get_user_model
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.backends.smtp import EmailBackend
from django.db import models
from django.template import TemplateSyntaxError
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.events.models import Event, EventAction
from authentik.flows.exceptions import StageInvalidException
from authentik.flows.models import ConfigurableStage, FriendlyNamedStage, Stage
from authentik.lib.config import CONFIG
from authentik.lib.models import SerializerModel
from authentik.lib.utils.errors import exception_to_string
from authentik.lib.utils.time import timedelta_string_validator
from authentik.stages.authenticator.models import SideChannelDevice
from authentik.stages.email.utils import TemplateEmailMessage


class EmailTemplates(models.TextChoices):
    """Templates used for rendering the Email"""

    EMAIL_OTP = (
        "email/email_otp.html",
        _("Email OTP"),
    )  # nosec


class AuthenticatorEmailStage(ConfigurableStage, FriendlyNamedStage, Stage):
    """Use Email-based authentication instead of authenticator-based."""

    use_global_settings = models.BooleanField(
        default=False,
        help_text=_(
            "When enabled, global Email connection settings will be used and "
            "connection settings below will be ignored."
        ),
    )

    host = models.TextField(default="localhost")
    port = models.IntegerField(default=25)
    username = models.TextField(default="", blank=True)
    password = models.TextField(default="", blank=True)
    use_tls = models.BooleanField(default=False)
    use_ssl = models.BooleanField(default=False)
    timeout = models.IntegerField(default=10)
    from_address = models.EmailField(default="system@authentik.local")

    token_expiry = models.TextField(
        default="minutes=30",
        validators=[timedelta_string_validator],
        help_text=_("Time the token sent is valid (Format: hours=3,minutes=17,seconds=300)."),
    )
    subject = models.TextField(default="authentik Sign-in code")
    template = models.TextField(default=EmailTemplates.EMAIL_OTP)

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.stages.authenticator_email.api import AuthenticatorEmailStageSerializer

        return AuthenticatorEmailStageSerializer

    @property
    def view(self) -> type[View]:
        from authentik.stages.authenticator_email.stage import AuthenticatorEmailStageView

        return AuthenticatorEmailStageView

    @property
    def component(self) -> str:
        return "ak-stage-authenticator-email-form"

    @property
    def backend_class(self) -> type[BaseEmailBackend]:
        """Get the email backend class to use"""
        return EmailBackend

    @property
    def backend(self) -> BaseEmailBackend:
        """Get fully configured Email Backend instance"""
        if self.use_global_settings:
            CONFIG.refresh("email.password")
            return self.backend_class(
                host=CONFIG.get("email.host"),
                port=CONFIG.get_int("email.port"),
                username=CONFIG.get("email.username"),
                password=CONFIG.get("email.password"),
                use_tls=CONFIG.get_bool("email.use_tls", False),
                use_ssl=CONFIG.get_bool("email.use_ssl", False),
                timeout=CONFIG.get_int("email.timeout"),
            )
        return self.backend_class(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            use_tls=self.use_tls,
            use_ssl=self.use_ssl,
            timeout=self.timeout,
        )

    def send(self, device: "EmailDevice"):
        # Lazy import here to avoid circular import
        from authentik.stages.email.tasks import send_mails

        # Compose the message using templates
        message = device._compose_email()
        return send_mails(device.stage, message)

    def __str__(self):
        return f"Email Authenticator Stage {self.name}"

    class Meta:
        verbose_name = _("Email Authenticator Setup Stage")
        verbose_name_plural = _("Email Authenticator Setup Stages")


class EmailDevice(SerializerModel, SideChannelDevice):
    """Email Device"""

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    email = models.EmailField()
    stage = models.ForeignKey(AuthenticatorEmailStage, on_delete=models.CASCADE)
    last_used = models.DateTimeField(auto_now=True)

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.stages.authenticator_email.api import EmailDeviceSerializer

        return EmailDeviceSerializer

    def _compose_email(self) -> TemplateEmailMessage:
        try:
            pending_user = self.user
            stage = self.stage
            email = self.email

            message = TemplateEmailMessage(
                subject=_(stage.subject),
                to=[(pending_user.name, email)],
                template_name=stage.template,
                template_context={
                    "user": pending_user,
                    "expires": self.valid_until,
                    "token": self.token,
                },
            )
            return message
        except TemplateSyntaxError as exc:
            Event.new(
                EventAction.CONFIGURATION_ERROR,
                message=_("Exception occurred while rendering E-mail template"),
                error=exception_to_string(exc),
                template=stage.template,
            ).from_http(self.request)
            raise StageInvalidException from exc

    def __str__(self):
        if not self.pk:
            return "New Email Device"
        return f"Email Device for {self.user_id}"

    class Meta:
        verbose_name = _("Email Device")
        verbose_name_plural = _("Email Devices")
        unique_together = (("user", "email"),)
