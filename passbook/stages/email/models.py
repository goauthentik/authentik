"""email stage models"""
from django.core.mail import get_connection
from django.core.mail.backends.base import BaseEmailBackend
from django.db import models
from django.utils.translation import gettext as _

from passbook.flows.models import Stage


class EmailTemplates(models.TextChoices):
    """Templates used for rendering the Email"""

    PASSWORD_RESET = (
        "stages/email/for_email/password_reset.html",
        _("Password Reset"),
    )  # nosec
    ACCOUNT_CONFIRM = (
        "stages/email/for_email/account_confirmation.html",
        _("Account Confirmation"),
    )


class EmailStage(Stage):
    """Sends an Email to the user with a token to confirm their Email address."""

    host = models.TextField(default="localhost")
    port = models.IntegerField(default=25)
    username = models.TextField(default="", blank=True)
    password = models.TextField(default="", blank=True)
    use_tls = models.BooleanField(default=False)
    use_ssl = models.BooleanField(default=False)
    timeout = models.IntegerField(default=10)
    from_address = models.EmailField(default="system@passbook.local")

    token_expiry = models.IntegerField(
        default=30, help_text=_("Time in minutes the token sent is valid.")
    )
    subject = models.TextField(default="passbook")
    template = models.TextField(
        choices=EmailTemplates.choices, default=EmailTemplates.PASSWORD_RESET
    )

    type = "passbook.stages.email.stage.EmailStageView"
    form = "passbook.stages.email.forms.EmailStageForm"

    @property
    def backend(self) -> BaseEmailBackend:
        """Get fully configured EMail Backend instance"""
        return get_connection(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            use_tls=self.use_tls,
            use_ssl=self.use_ssl,
            timeout=self.timeout,
        )

    def __str__(self):
        return f"Email Stage {self.name}"

    class Meta:

        verbose_name = _("Email Stage")
        verbose_name_plural = _("Email Stages")
