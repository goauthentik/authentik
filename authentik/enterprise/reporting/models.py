"""Reporting models"""

from uuid import uuid4

from celery.schedules import crontab
from django.db import models
from django.utils.translation import gettext_lazy as _

from authentik.events.models import NotificationTransport
from authentik.lib.models import InheritanceForeignKey, SerializerModel
from authentik.policies.models import PolicyBindingModel


class OutputType(models.TextChoices):
    """Different choices in which a report can be 'rendered'"""

    csv = "csv"
    pdf = "pdf"


class Report(SerializerModel, PolicyBindingModel):
    """A report with a defined list of components, which can run on a schedule"""

    name = models.TextField()

    schedule = models.TextField()

    # User under which permissions the queries are run,
    # when no user is selected the report is inactive
    run_as = models.ForeignKey(
        "authentik_core.user", on_delete=models.SET_DEFAULT, default=None, null=True
    )
    components = models.ManyToManyField(
        "ReportComponent", through="ReportComponentBinding", related_name="bindings", blank=True
    )
    output_type = models.TextField(choices=OutputType.choices)
    # Use notification transport to send report result (either link for webhook based?
    # maybe send full csv?) or fully rendered PDF via Email
    # when no transport is selected, reports are not sent anywhere but can be retrieved in authentik
    delivery = models.ForeignKey(
        NotificationTransport, on_delete=models.SET_DEFAULT, default=None, null=True
    )

    def __str__(self) -> str:
        return self.name

    def get_celery_schedule(self) -> crontab:
        return crontab(*self.schedule.split())

    class Meta:
        verbose_name = _("Report")
        verbose_name_plural = _("Reports")


class ReportComponentBinding(SerializerModel, PolicyBindingModel):
    """Binding of a component to a report"""

    binding_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    enabled = models.BooleanField(default=True)

    layout_x = models.PositiveIntegerField(default=0)
    layout_y = models.PositiveIntegerField(default=0)

    target = models.ForeignKey("Report", on_delete=models.CASCADE)
    widget = InheritanceForeignKey("ReportComponent", on_delete=models.CASCADE, related_name="+")

    def __str__(self) -> str:
        return f"Binding from {self.report.name} to {self.widget}"

    class Meta:
        verbose_name = _("Report Component Binding")
        verbose_name_plural = _("Report Component Bindings")
        unique_together = ("target", "widget")


class ReportComponent(SerializerModel):
    """An individual component of a report, a query or graph, etc"""

    widget_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    def __str__(self) -> str:
        return super().__str__()

    class Meta:
        verbose_name = _("Report Component")
        verbose_name_plural = _("Report Components")
