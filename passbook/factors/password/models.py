"""password factor models"""
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _

from passbook.core.models import Factor, Policy, User
from passbook.core.types import UIUserSettings


class PasswordFactor(Factor):
    """Password-based Django-backend Authentication Factor"""

    backends = ArrayField(models.TextField())
    password_policies = models.ManyToManyField(Policy, blank=True)
    reset_factors = models.ManyToManyField(
        Factor, blank=True, related_name="reset_factors"
    )

    type = "passbook.factors.password.factor.PasswordFactor"
    form = "passbook.factors.password.forms.PasswordFactorForm"

    @property
    def ui_user_settings(self) -> UIUserSettings:
        return UIUserSettings(
            name="Change Password",
            icon="pficon-key",
            view_name="passbook_core:user-change-password",
        )

    def password_passes(self, user: User) -> bool:
        """Return true if user's password passes, otherwise False or raise Exception"""
        for policy in self.policies.all():
            if not policy.passes(user):
                return False
        return True

    def __str__(self):
        return "Password Factor %s" % self.slug

    class Meta:

        verbose_name = _("Password Factor")
        verbose_name_plural = _("Password Factors")
