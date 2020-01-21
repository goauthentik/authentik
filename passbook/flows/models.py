from django.db import models
from passbook.lib.models import UUIDModel
from passbook.core.models import Factor


class FlowToFactor(UUIDModel):

    flow = models.ForeignKey("Flow", on_delete=models.CASCADE)
    factor = models.ForeignKey(Factor, on_delete=models.CASCADE)
    order = models.IntegerField()

    class Meta:

        unique_together = (("flow", "factor", "order"),)


class Flow(UUIDModel):

    slug = models.SlugField(unique=True)
    factors = models.ManyToManyField(Factor, through=FlowToFactor)
    # TODO: requireed_policies to apply flows to authenticated users only?
