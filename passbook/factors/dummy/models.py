"""dummy factor models"""
from django.utils.translation import gettext as _

from passbook.core.models import Factor


class DummyFactor(Factor):
    """Dummy factor, mostly used to debug"""

    type = "passbook.factors.dummy.factor.DummyFactor"
    form = "passbook.factors.dummy.forms.DummyFactorForm"

    def __str__(self):
        return f"Dummy Factor {self.slug}"

    class Meta:

        verbose_name = _("Dummy Factor")
        verbose_name_plural = _("Dummy Factors")
