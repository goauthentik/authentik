from urllib.parse import urlsplit

from django.contrib.auth import get_user_model
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.backends.smtp import EmailBackend
from django.db import models
from django.http import HttpRequest
from django.template import Context, Template, TemplateSyntaxError
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.brands.utils import get_brand_for_request
from authentik.core.types import UserSettingSerializer
from authentik.events.models import Event, EventAction
from authentik.flows.exceptions import StageInvalidException
from authentik.flows.models import ConfigurableStage, FriendlyNamedStage, Stage
from authentik.lib.config import CONFIG
from authentik.lib.models import SerializerModel
from authentik.lib.utils.time import timedelta_string_validator
from authentik.stages.authenticator.models import SideChannelDevice, ThrottlingMixin
from authentik.stages.email.models import EmailTemplates
from authentik.stages.email.utils import TemplateEmailMessage


class AuthenticatorEmailStage(ConfigurableStage, FriendlyNamedStage, Stage):
    """Setup Email-based authentication for the user."""

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
    subject = models.TextField(default="Your verification code is {{ token }}")
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

    def ui_user_settings(self) -> UserSettingSerializer | None:
        return UserSettingSerializer(
            data={
                "title": self.friendly_name or str(self._meta.verbose_name),
                "component": "ak-user-settings-authenticator-email",
            }
        )

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

    def send(self, device: EmailDevice, request: HttpRequest | None = None):
        # Lazy import here to avoid circular import
        from authentik.stages.email.tasks import send_mails

        # Compose the message using templates
        message = device._compose_email(request)
        return send_mails(device.stage, message)

    def __str__(self):
        return f"Email Authenticator Stage {self.name}"

    class Meta:
        verbose_name = _("Email Authenticator Setup Stage")
        verbose_name_plural = _("Email Authenticator Setup Stages")


class EmailDevice(SerializerModel, ThrottlingMixin, SideChannelDevice):
    """Email Device"""

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    email = models.EmailField()
    stage = models.ForeignKey(AuthenticatorEmailStage, on_delete=models.PROTECT)
    last_used = models.DateTimeField(auto_now=True)

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.stages.authenticator_email.api import EmailDeviceSerializer

        return EmailDeviceSerializer

    def verify_token(self, token: str) -> bool:
        verify_allowed, _ = self.verify_is_allowed()
        if verify_allowed:
            verified = super().verify_token(token)

            if verified:
                self.throttle_reset()
            else:
                self.throttle_increment()
        else:
            verified = False

        return verified

    def _compose_email(self, request: HttpRequest | None = None) -> TemplateEmailMessage:
        """Compose the code email, with the code in the subject and an OTP-Token header."""
        user = self.user
        stage = self.stage
        headers = {}
        if origin := otp_token_origin(request):
            # https://datatracker.ietf.org/doc/html/draft-goto-otp-token-01
            headers["OTP-Token"] = f'"{self.token}"; origin="{origin}"'
        try:
            # The subject is admin-editable, so it only gets plain values, not model instances.
            subject_context = Context(
                {"token": self.token, "username": user.username},
                autoescape=False,
            )
            return TemplateEmailMessage(
                subject=Template(str(_(stage.subject))).render(subject_context),
                to=[(user.name, self.email)],
                language=user.locale(request),
                template_name=stage.template,
                template_context={
                    "user": user,
                    "expires": self.valid_until,
                    "token": self.token,
                },
                headers=headers,
                sensitive_values=[self.token],
            )
        except TemplateSyntaxError as exc:
            event = Event.new(
                EventAction.CONFIGURATION_ERROR,
                message=_("Exception occurred while rendering E-mail template"),
                template=stage.template,
            ).with_exception(exc)
            if request:
                event.from_http(request)
            else:
                event.save()
            raise StageInvalidException from exc

    def __str__(self):
        if not self.pk:
            return "New Email Device"
        return f"Email Device for {self.user_id}"

    class Meta:
        verbose_name = _("Email Device")
        verbose_name_plural = _("Email Devices")
        unique_together = (("user", "email"),)


def otp_token_origin(request: HttpRequest | None) -> str | None:
    """The origin of the request, if it is https and its host matches its brand's domain."""
    if not request or not request.is_secure():
        return None
    brand = getattr(request, "brand", None) or get_brand_for_request(request)
    host = urlsplit(f"//{request.get_host()}")
    hostname = (host.hostname or "").rstrip(".")
    domain = brand.domain.lower()
    if hostname != domain and not hostname.endswith(f".{domain}"):
        return None
    port = f":{host.port}" if host.port not in (None, 443) else ""
    return f"https://{hostname}{port}"
