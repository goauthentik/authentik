"""email factor models"""
from django.core.mail.backends.smtp import EmailBackend
from django.db import models
from django.utils.translation import gettext as _

from passbook.core.models import Factor


class EmailFactor(Factor):
    """email factor"""

    host = models.TextField(default="localhost")
    port = models.IntegerField(default=25)
    username = models.TextField(default="", blank=True)
    password = models.TextField(default="", blank=True)
    use_tls = models.BooleanField(default=False)
    use_ssl = models.BooleanField(default=False)
    timeout = models.IntegerField(default=10)

    ssl_keyfile = models.TextField(default=None, blank=True, null=True)
    ssl_certfile = models.TextField(default=None, blank=True, null=True)

    from_address = models.EmailField(default="system@passbook.local")

    type = "passbook.factors.email.factor.EmailFactorView"
    form = "passbook.factors.email.forms.EmailFactorForm"

    @property
    def backend(self) -> EmailBackend:
        """Get fully configured EMail Backend instance"""
        return EmailBackend(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            use_tls=self.use_tls,
            use_ssl=self.use_ssl,
            timeout=self.timeout,
            ssl_certfile=self.ssl_certfile,
            ssl_keyfile=self.ssl_keyfile,
        )

    def __str__(self):
        return f"Email Factor {self.slug}"

    class Meta:

        verbose_name = _("Email Factor")
        verbose_name_plural = _("Email Factors")
