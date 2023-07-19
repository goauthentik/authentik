"""email stage models"""
from os import R_OK, access
from pathlib import Path
from typing import Type

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.backends.smtp import EmailBackend
from django.db import models
from django.utils.translation import gettext as _
from django.views import View
from rest_framework.serializers import BaseSerializer
from structlog.stdlib import get_logger

from authentik.flows.models import Stage
from authentik.lib.config import CONFIG

LOGGER = get_logger()


class EmailTemplates(models.TextChoices):
    """Templates used for rendering the Email"""

    PASSWORD_RESET = (
        "email/password_reset.html",
        _("Password Reset"),
    )  # nosec
    ACCOUNT_CONFIRM = (
        "email/account_confirmation.html",
        _("Account Confirmation"),
    )


def get_template_choices():
    """Get all available Email templates, including dynamically mounted ones.
    Directories are taken from TEMPLATES.DIR setting"""
    static_choices = EmailTemplates.choices

    dirs = [Path(x) for x in settings.TEMPLATES[0]["DIRS"]]
    for template_dir in dirs:
        if not template_dir.exists() or not template_dir.is_dir():
            continue
        for template in template_dir.glob("**/*.html"):
            path = str(template)
            if not access(path, R_OK):
                LOGGER.warning("Custom template file is not readable, check permissions", path=path)
                continue
            rel_path = template.relative_to(template_dir)
            static_choices.append((str(rel_path), f"Custom Template: {rel_path}"))
    return static_choices


class EmailStage(Stage):
    """Sends an Email to the user with a token to confirm their Email address."""

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
    template = models.TextField(default=EmailTemplates.PASSWORD_RESET)

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.stages.email.api import EmailStageSerializer

        return EmailStageSerializer

    @property
    def type(self) -> type[View]:
        from authentik.stages.email.stage import EmailStageView

        return EmailStageView

    @property
    def component(self) -> str:
        return "ak-stage-email-form"

    @property
    def backend_class(self) -> Type[BaseEmailBackend]:
        """Get the email backend class to use"""
        return EmailBackend

    @property
    def backend(self) -> BaseEmailBackend:
        """Get fully configured Email Backend instance"""
        if self.use_global_settings:
            CONFIG.refresh("email.password")
            return self.backend_class(
                host=CONFIG.get("email.host"),
                port=int(CONFIG.get("email.port")),
                username=CONFIG.get("email.username"),
                password=CONFIG.get("email.password"),
                use_tls=CONFIG.get_bool("email.use_tls", False),
                use_ssl=CONFIG.get_bool("email.use_ssl", False),
                timeout=int(CONFIG.get("email.timeout")),
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

    def __str__(self):
        return f"Email Stage {self.name}"

    class Meta:
        verbose_name = _("Email Stage")
        verbose_name_plural = _("Email Stages")
