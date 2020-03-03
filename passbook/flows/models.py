from django.db import models
from django.utils.translation import gettext_lazy as _

from passbook.core.models import Factor
from passbook.lib.models import UUIDModel


# TODO: Add PolicyModel
class FactorBinding(UUIDModel):

    flow = models.ForeignKey("Flow", on_delete=models.CASCADE)
    factor = models.ForeignKey(Factor, on_delete=models.CASCADE)
    order = models.IntegerField()

    class Meta:

        unique_together = (("flow", "factor", "order"),)


class Flow(UUIDModel):

    slug = models.SlugField(unique=True)
    factors = models.ManyToManyField(Factor, through=FactorBinding)
    designation = models.CharField(
        max_length=100,
        choices=(
            ("enroll", _("Enroll")),
            ("auth", _("Authentication")),
            ("recovery", _("Recovery")),
        ),
    )

    def __str__(self):
        return f"Flow {self.slug}"

    class Meta:

        verbose_name = _("Flow")
        verbose_name_plural = _("Flows")
