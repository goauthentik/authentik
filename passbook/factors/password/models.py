"""password factor models"""
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _

from passbook.core.models import Factor, Policy, User


class PasswordFactor(Factor):
    """Password-based Django-backend Authentication Factor"""

    backends = ArrayField(models.TextField())
    password_policies = models.ManyToManyField(Policy, blank=True)

    type = 'passbook.factors.password.factor.PasswordFactor'
    form = 'passbook.factors.password.forms.PasswordFactorForm'

    def has_user_settings(self):
        return _('Change Password'), 'pficon-key', 'passbook_core:user-change-password'

    def password_passes(self, user: User) -> bool:
        """Return true if user's password passes, otherwise False or raise Exception"""
        for policy in self.policies.all():
            if not policy.passes(user):
                return False
        return True

    def __str__(self):
        return "Password Factor %s" % self.slug

    class Meta:

        verbose_name = _('Password Factor')
        verbose_name_plural = _('Password Factors')
