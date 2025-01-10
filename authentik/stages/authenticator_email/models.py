from django.contrib.auth import get_user_model
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.backends.smtp import EmailBackend
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer
from structlog.stdlib import get_logger

from authentik.flows.models import ConfigurableStage, FriendlyNamedStage, Stage
from authentik.lib.config import CONFIG
from authentik.lib.models import SerializerModel
from authentik.stages.authenticator.models import SideChannelDevice

LOGGER = get_logger()

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

    activate_user_on_success = models.BooleanField(
        default=False, help_text=_("Activate users upon completion of stage.")
    )

    token_expiry = models.IntegerField(
        default=30, help_text=_("Time in minutes the token sent is valid.")
    )
    subject = models.TextField(default="authentik")
    # verify_only ??

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
        return "ak-stage-authenticator-email"

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

    def send(self, message: str, device: "EmailDevice"):
        return self.backend.send_mail(
            subject=self.subject,
            message=message,
            from_email=self.from_address,
            recipient_list=[device.email],
        )

    def __str__(self):
        return f"Email Stage {self.name}"

    class Meta:
        verbose_name = _("Email Autherenticator Stage")
        verbose_name_plural = _("Email Authenticator Stages")


class EmailDevice(SerializerModel, SideChannelDevice):
    """Email Device"""
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    email = models.EmailField()
    stage = models.ForeignKey(AuthenticatorEmailStage, on_delete=models.CASCADE)
    last_used = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Email Device")
        verbose_name_plural = _("Email Devices")
        unique_together = (("user", "email"),)

    def __str__(self):
        return f"Email Device for {self.user}"
