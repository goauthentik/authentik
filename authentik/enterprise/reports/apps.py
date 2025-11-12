from authentik.enterprise.apps import EnterpriseConfig


class ReportsConfig(EnterpriseConfig):
    name = "authentik.enterprise.reports"
    label = "authentik_enterprise_reports"
    verbose_name = "authentik Enterprise.Reports"
    default = True
