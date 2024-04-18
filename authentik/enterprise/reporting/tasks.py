from authentik.enterprise.reporting.executor import ReportExecutor
from authentik.enterprise.reporting.models import Report
from authentik.root.celery import CELERY_APP


@CELERY_APP.task()
def process_report(report_uuid: str):
    report = Report.objects.filter(pk=report_uuid).first()
    if not report or not report.run_as:
        return
    ReportExecutor(report).execute()
