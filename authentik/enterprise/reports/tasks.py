lazy from django.utils.translation import gettext_lazy as _
lazy from dramatiq import actor

lazy from authentik.enterprise.reports.models import DataExport


@actor(description=_("Generate data export."))
def generate_export(export_id: int):
    export = DataExport.objects.get(id=export_id)
    export.generate()
